export async function apiCall(endpoint, options = {}) {
  const response = await fetch(endpoint, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  const data = await response.json();
  return { response, data };
}

// =========================
// Authentication API
// =========================

export async function login(username, password) {
  return apiCall("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export async function register(username, password) {
  return apiCall("/api/auth/register", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export async function logout() {
  return apiCall("/api/auth/logout", {
    method: "GET",
  });
}

export async function getCurrentUser() {
  return apiCall("/api/me", {
    method: "GET",
  });
}

// =========================
// Chat API
// =========================

export async function createChat(withUsername) {
  return apiCall("/api/chat/create", {
    method: "POST",
    body: JSON.stringify({ with: withUsername }),
  });
}

export async function getChatSessions() {
  return apiCall("/api/chat/sessions", {
    method: "GET",
  });
}

export async function getMessages(sessionId) {
  return apiCall(`/api/chat/${sessionId}`, {
    method: "GET",
  });
}

export async function sendMessage(sessionId, message) {
  return apiCall(`/api/chat/${sessionId}/send`, {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}

export async function getEmoticon(sessionId, filename) {
  return apiCall("/api/chat/emoticons", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, filename }),
  });
}

export async function sendNudge(sessionId, toUsername, fromUsername) {
  const payload =
    `INVITE MSNMSGR:${toUsername}@msn.com MSNSLP/1.0\r\n` +
    `To: <msnmsgr:${toUsername}@msn.com>\r\n` +
    `From: <msnmsgr:${fromUsername}@msn.com>\r\n` +
    `Call-ID: ${sessionId}\r\n` +
    `CSeq: 0\r\n` +
    `Content-Type: text/x-msnmsgr-datacast\r\n` +
    `\r\n` +
    `ID: 1`;

  const response = await fetch("/api/chat/event", {
    method: "POST",
    body: payload,
    credentials: "include",
    headers: {
      "Content-Type": "text/x-msnmsgr-datacast",
    },
  });

  const data = await response.json();
  return { response, data };
}

function buildP2PHeader(sessionId, messageSize, totalSize = 0, flags = 0) {
  const buffer = new ArrayBuffer(48);
  const view = new DataView(buffer);

  view.setUint32(0, sessionId, true);
  view.setUint32(4, 0, true);
  view.setBigUint64(8, 0n, true);
  view.setBigUint64(16, BigInt(totalSize), true);
  view.setUint32(24, messageSize, true);
  view.setUint32(28, flags, true);
  view.setUint32(32, 0, true);
  view.setUint32(36, 0, true);
  view.setBigUint64(40, 0n, true);

  return new Uint8Array(buffer);
}

function stringToBytes(str) {
  const encoder = new TextEncoder();
  return encoder.encode(str);
}

function concatBytes(...arrays) {
  const totalLength = arrays.reduce((acc, arr) => acc + arr.length, 0);
  const result = new Uint8Array(totalLength);
  let offset = 0;

  for (const arr of arrays) {
    result.set(arr, offset);
    offset += arr.length;
  }

  return result;
}

export async function sendEmoticon(
  sessionId,
  toUsername,
  fromUsername,
  imageFile,
) {
  const imageData = await imageFile.arrayBuffer();
  const imageBytes = new Uint8Array(imageData);

  const xmlContext = `<msnobj Creator="${fromUsername}" Type="2" />`;
  const b64Context = btoa(xmlContext);

  const inviteText =
    `INVITE MSNMSGR:${toUsername}@msn.com MSNSLP/1.0\r\n` +
    `To: <msnmsgr:${toUsername}@msn.com>\r\n` +
    `From: <msnmsgr:${fromUsername}@msn.com>\r\n` +
    `Call-ID: ${sessionId}\r\n` +
    `CSeq: 0\r\n` +
    `Content-Type: application/x-msnmsgrp2p\r\n` +
    `Context: ${b64Context}\r\n` +
    `\r\n`;
  const inviteBytes = stringToBytes(inviteText);

  const legitimateSize = inviteBytes.length + 48 + imageBytes.length;

  const header1 = buildP2PHeader(100, inviteBytes.length, legitimateSize, 0x01);

  const header2 = buildP2PHeader(
    100,
    imageBytes.length,
    imageBytes.length,
    0x02,
  );

  const fullBody = concatBytes(header1, inviteBytes, header2, imageBytes);

  const response = await fetch("/api/chat/event", {
    method: "POST",
    body: fullBody,
    credentials: "include",
    headers: {
      "Content-Type": "application/x-msnmsgrp2p",
    },
  });

  const data = await response.json();
  return { response, data };
}
