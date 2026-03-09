import express from "express";
import http from "http";

const app = express();

// ===== Config =====

const BACKEND_HOST = process.env.BACKEND_HOST || "127.0.0.1";
const BACKEND_PORT = Number(process.env.BACKEND_PORT || 8000);
const MAX_BODY_SIZE = 10 * 1024 * 1024; // 10 MB

const httpAgent = new http.Agent({
  keepAlive: true,
  keepAliveMsecs: 10_000,
  maxSockets: 10,
  maxFreeSockets: 5,
});

// ===== Helpers =====

function extractMsnTotalSize(buff) {
  const BIN_HDR_SIZE = 48;
  if (buff.length < BIN_HDR_SIZE) return null;
  try {
    const totalSize = buff.readBigUInt64LE(16);
    return Number(totalSize) + BIN_HDR_SIZE;
  } catch (e) {
    return null;
  }
}

function isLocalhost(req) {
  const ip = req.socket.remoteAddress;
  return ip === "::1" || ip?.startsWith("127.") || ip === "::ffff:127.0.0.1";
}

function proxyRequest(req, res, { modifyHeaders = null } = {}) {
  const chunks = [];
  let total = 0;

  if (req.method !== "GET" && req.method !== "HEAD") {
    req.on("data", (chunk) => {
      if (total + chunk.length > MAX_BODY_SIZE) {
        req.destroy();
        if (!res.headersSent) {
          return res.status(413).json({ ok: false, error: "body_too_large" });
        }
        return;
      }
      chunks.push(chunk);
      total += chunk.length;
    });
  } else {
    req.resume();
  }

  req.on("end", () => {
    const body = chunks.length > 0 ? Buffer.concat(chunks) : null;

    let finalHeaders = { ...req.headers };

    if (modifyHeaders) {
      finalHeaders = modifyHeaders(finalHeaders, body);
    }

    if (body && !finalHeaders["content-length"]) {
      finalHeaders["content-length"] = body.length;
    }

    delete finalHeaders["transfer-encoding"];
    delete finalHeaders["proxy-connection"];
    delete finalHeaders.upgrade;
    delete finalHeaders.te;
    delete finalHeaders.trailer;

    const options = {
      host: BACKEND_HOST,
      port: BACKEND_PORT,
      method: req.method,
      path: req.originalUrl,
      headers: finalHeaders,
      agent: httpAgent,
    };

    const backendReq = http.request(options, (backendRes) => {
      res.status(backendRes.statusCode);

      for (const [key, value] of Object.entries(backendRes.headers)) {
        if (
          !["connection", "transfer-encoding", "server"].includes(
            key.toLowerCase(),
          )
        ) {
          res.setHeader(key, value);
        }
      }

      backendRes.pipe(res);
    });

    backendReq.on("error", (_err) => {
      if (!res.headersSent) {
        res.status(502).json({ ok: false, error: "bad_gateway" });
      }
    });

    backendReq.on("timeout", () => {
      backendReq.destroy();
      if (!res.headersSent) {
        res.status(504).json({ ok: false, error: "gateway_timeout" });
      }
    });

    if (body) {
      backendReq.write(body);
    }

    backendReq.end();
  });

  req.on("error", (_err) => {
    if (!res.headersSent) {
      res.status(400).json({ ok: false, error: "bad_request" });
    }
  });
}

// ===== Middleware =====

app.use((req, res, next) => {
  if (req.headers["transfer-encoding"]) {
    return res.status(400).json({
      ok: false,
      error: "transfer_encoding_not_allowed",
    });
  }

  const cl = req.headers["content-length"];
  if (cl) {
    const num = parseInt(cl, 10);
    if (isNaN(num) || num < 0 || num > MAX_BODY_SIZE) {
      return res.status(400).json({
        ok: false,
        error: "invalid_content_length",
      });
    }
  }

  for (const [key, value] of Object.entries(req.headers)) {
    if (typeof value === "string" && /[\r\n]/.test(value)) {
      return res.status(400).json({
        ok: false,
        error: "invalid_header_value",
        header: key,
      });
    }
  }

  next();
});

// ===== Routes =====

app.all("/api/export/chat", (req, res, next) => {
  if (!isLocalhost(req)) {
    return res.status(403).json({ ok: false, error: "WIP: local access only" });
  }
  next();
});

app.post("/api/chat/event", (req, res) => {
  proxyRequest(req, res, {
    modifyHeaders: (headers, body) => {
      if (!body) return headers;

      const contentType = (headers["content-type"] || "").toLowerCase();
      if (contentType === "application/x-msnmsgrp2p") {
        const msnSize = extractMsnTotalSize(body);
        return {
          ...headers,
          "content-length": msnSize ?? body.length,
        };
      } else {
        return headers;
      }
    },
  });
});

app.use((req, res) => {
  proxyRequest(req, res);
});

// ===== Server =====

app.listen(process.env.PORT || 80, () => {
  console.log(
    `[gateway] listening on :${process.env.PORT || 80} -> ${BACKEND_HOST}:${BACKEND_PORT}`,
  );
});
