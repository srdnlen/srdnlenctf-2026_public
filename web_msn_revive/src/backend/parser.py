"""MSNSLP parser implementation."""

import base64
import io
import struct
from dataclasses import dataclass
from typing import Dict, Literal, Optional, Tuple, Union
from defusedxml import ElementTree as DET

from PIL import Image

# =========================
# Exceptions / Data Models
# =========================


class MSNSLPError(Exception):
    """Generic parsing/validation error."""


@dataclass(frozen=True)
class SlpHeaders:
    start_line: str
    headers: Dict[str, str]


@dataclass(frozen=True)
class P2PHeaderV2:
    """MSNMSGRP2P (P2P v2) 48-byte header.

    This struct is widely implemented as a fixed 48-byte little-endian header:

      SessionID      (uint32)  - P2P session identifier
      Identifier     (uint32)  - message/packet identifier
      Offset         (uint64)  - byte offset inside the full object
      TotalSize      (uint64)  - total object size in bytes
      MessageSize    (uint32)  - size of this chunk's payload in bytes
      Flags          (uint32)  - control flags
      AckSessionID   (uint32)  - ack session id
      AckUniqueID    (uint32)  - ack unique id
      AckDataSize    (uint64)  - acked data size
    """

    session_id: int
    identifier: int
    offset: int
    total_size: int
    message_size: int
    flags: int
    ack_session_id: int
    ack_unique_id: int
    ack_data_size: int

    _FMT = "<IIQQIIIIQ"
    _SIZE = 48

    @classmethod
    def from_bytes(cls, data: bytes, max_message_size: int) -> "P2PHeaderV2":
        if len(data) < cls._SIZE:
            raise MSNSLPError("missing_p2p_header")

        try:
            (
                session_id,
                identifier,
                offset,
                total_size,
                message_size,
                flags,
                ack_session_id,
                ack_unique_id,
                ack_data_size,
            ) = struct.unpack(cls._FMT, data[: cls._SIZE])
        except struct.error as e:
            raise MSNSLPError("bad_p2p_header") from e

        # Sanity checks (values are unsigned but keep guards explicit)
        if offset < 0 or total_size < 0 or message_size < 0:
            raise MSNSLPError("bad_p2p_sizes")

        # Reject absurd sizes to avoid allocation / slicing abuse
        if message_size > 10 * int(max_message_size):
            raise MSNSLPError("p2p_message_size_absurd")

        # Basic consistency for chunked semantics
        if message_size > total_size and total_size != 0:
            raise MSNSLPError("p2p_message_larger_than_total")

        return cls(
            session_id=session_id,
            identifier=identifier,
            offset=offset,
            total_size=total_size,
            message_size=message_size,
            flags=flags,
            ack_session_id=ack_session_id,
            ack_unique_id=ack_unique_id,
            ack_data_size=ack_data_size,
        )


@dataclass(frozen=True)
class MsnObject:
    attrs: Dict[str, str]


@dataclass(frozen=True)
class NudgeEvent:
    type: Literal["nudge"] = "nudge"
    call_id: Optional[str] = None
    from_user: Optional[str] = None


@dataclass(frozen=True)
class EmoticonEvent:
    type: Literal["emoticon"] = "emoticon"
    call_id: Optional[str] = None
    from_user: Optional[str] = None
    p2p_header_1: P2PHeaderV2 = None  # type: ignore
    p2p_header_2: P2PHeaderV2 = None  # type: ignore
    msn_object: Optional[MsnObject] = None
    mime: str = ""
    data: bytes = b""


@dataclass(frozen=True)
class UnknownEvent:
    type: Literal["unknown"] = "unknown"
    content_type: str = ""


ParsedEvent = Union[NudgeEvent, EmoticonEvent, UnknownEvent]


# ======================
# Parser Implementation
# ======================


class MSNSLPParser:
    """MSNSLP parser"""

    _P2P_SIZE = P2PHeaderV2._SIZE

    def __init__(self, max_payload_size: int = 10 * 1024 * 1024) -> None:
        self.max_payload_size = max_payload_size

    def parse(self, raw: bytes, content_type: str) -> ParsedEvent:
        if not raw:
            raise MSNSLPError("empty_body")

        ctype = (content_type or "").lower().strip()

        # 1. NUDGE
        if "text/x-msnmsgr-datacast" in ctype:
            return self._handle_nudge(raw)

        # 2. EMOTICON
        elif "application/x-msnmsgrp2p" in ctype:
            return self._handle_p2p(raw)

        return UnknownEvent(content_type=content_type)

    # ----------- Handlers --------------------

    def _handle_nudge(self, raw: bytes) -> NudgeEvent:
        slp, rest = self._parse_slp(raw)

        decoded_body = rest.decode("utf-8", errors="ignore").lower()
        if "id: 1" in decoded_body:
            return NudgeEvent(
                call_id=slp.headers.get("call-id"),
                from_user=self._extract_username(slp.headers),
            )

        raise MSNSLPError("missing_nudge_id")

    def _handle_p2p(self, raw: bytes) -> EmoticonEvent:
        cursor = 0

        # Parse first P2P header and payload (SLP)
        if len(raw) < self._P2P_SIZE:
            raise MSNSLPError("missing_p2p_header_1")

        p2p_1 = P2PHeaderV2.from_bytes(
            raw[cursor:], max_message_size=self.max_payload_size
        )
        cursor += self._P2P_SIZE

        end_p1 = cursor + p2p_1.message_size
        if len(raw) < end_p1:
            raise MSNSLPError("truncated_p2p_payload_1")

        invite_blob = raw[cursor:end_p1]
        cursor = end_p1

        slp, _ = self._parse_slp(invite_blob)
        call_id = slp.headers.get("call-id")
        from_user = self._extract_username(slp.headers)
        msn_object = self._parse_msn_object(slp.headers.get("context"))

        # Parse second P2P header and payload (data)
        if len(raw) < cursor + self._P2P_SIZE:
            raise MSNSLPError("missing_p2p_header_2")

        p2p_2 = P2PHeaderV2.from_bytes(
            raw[cursor:], max_message_size=self.max_payload_size
        )
        cursor += self._P2P_SIZE

        end_p2 = cursor + p2p_2.message_size

        if len(raw) < end_p2:
            raise MSNSLPError("truncated_p2p_payload_2")

        png_data = raw[cursor:end_p2]

        mime = self._infer_image_mime(png_data)

        return EmoticonEvent(
            call_id=call_id,
            from_user=from_user,
            p2p_header_1=p2p_1,
            p2p_header_2=p2p_2,
            msn_object=msn_object,
            mime=mime,
            data=png_data,
        )

    # ----------- Helpers ---------------------

    def _parse_slp(self, blob: bytes) -> Tuple[SlpHeaders, bytes]:
        idx = blob.find(b"\r\n\r\n")
        if idx == -1:
            raise MSNSLPError("missing_headers_end")

        try:
            header_part = blob[:idx].decode("utf-8")
        except UnicodeDecodeError:
            raise MSNSLPError("bad_header_encoding")

        rest = blob[idx + 4 :]

        lines = header_part.splitlines()
        start_line = lines[0].strip() if lines else ""
        headers = {}
        for line in lines[1:]:
            if ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip().lower()] = v.strip()

        return SlpHeaders(start_line, headers), rest

    def _parse_msn_object(self, context: Optional[str]) -> Optional[MsnObject]:
        if not context:
            return None
        try:
            raw = base64.b64decode(context, validate=True)
        except Exception as e:
            raise MSNSLPError("bad_context") from e

        try:
            root = DET.fromstring(raw.decode("utf-8"))
        except Exception as e:
            print(f"XML parsing error: {e}", flush=True)
            raise MSNSLPError("bad_msnobject_xml") from e

        if root.tag.lower() not in ("msnobj", "msnobject"):
            raise MSNSLPError("unexpected_msnobject_tag")

        return MsnObject(attrs=dict(root.attrib))

    def _infer_image_mime(self, data: bytes) -> str:
        try:
            with Image.open(io.BytesIO(data)) as im:
                im.verify()
                fmt = (im.format or "").upper()
                if fmt not in ("PNG", "GIF", "JPG"):
                    raise MSNSLPError("unsupported_image_format")
                return f"image/{fmt.lower()}"
        except MSNSLPError:
            raise
        except Exception as e:
            raise MSNSLPError("invalid_image_data") from e

    def _extract_username(self, headers: Dict[str, str]) -> Optional[str]:
        raw = headers.get("from")
        if not raw:
            return None
        if "<" in raw and ">" in raw:
            raw = raw.split("<")[1].split(">")[0]
        if ":" in raw:
            raw = raw.split(":")[-1]
        if "@" in raw:
            raw = raw.split("@")[0]

        return raw.strip()
