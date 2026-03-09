import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from http import HTTPStatus
from typing import Any

from app import login_manager
from flask import (
    Blueprint,
    Response,
    current_app,
    jsonify,
    request,
    send_from_directory,
)
from flask_login import current_user, login_required, login_user, logout_user
from models import ChatSession, Message, User, db
from parser import MSNSLPError, MSNSLPParser
from utils import is_member, render_export
from werkzeug.security import check_password_hash, generate_password_hash

api = Blueprint("api", __name__)


@dataclass
class APIResponse:
    """Uniform API response structure"""

    ok: bool
    data: dict | None = None
    error: str | None = None
    error_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"ok": self.ok}

        if self.data is not None:
            result["data"] = self.data

        if self.error:
            result["error"] = self.error
            if self.error_code:
                result["error_code"] = self.error_code

        return result

    def to_response(self, status_code: int) -> tuple:
        return jsonify(self.to_dict()), status_code


def success(data: dict, status_code: HTTPStatus = HTTPStatus.OK) -> tuple:
    return APIResponse(ok=True, data=data).to_response(status_code)


def error(message: str, code: str, status_code: HTTPStatus) -> tuple:
    return APIResponse(ok=False, error=message, error_code=code).to_response(
        status_code
    )


@login_manager.user_loader
def load_user(user_id) -> Any | None:
    user = User.query.get(int(user_id))
    return user


@login_manager.unauthorized_handler
def unauthorized_callback() -> tuple[Response, int]:
    return error("unauthorized", "UNAUTHORIZED", HTTPStatus.UNAUTHORIZED)


@api.after_request
def add_security_headers(response: Response) -> Response:
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'self'"

    return response


@api.app_errorhandler(500)
def internal_error(err: Any) -> tuple[Response, int]:
    current_app.logger.error(f"Internal server error: {err}")
    return error(
        "internal_server_error",
        "INTERNAL_SERVER_ERROR",
        HTTPStatus.INTERNAL_SERVER_ERROR,
    )


@api.app_errorhandler(404)
def not_found_error(err: Any) -> tuple[Response, int]:
    return error("not_found", "NOT_FOUND", HTTPStatus.NOT_FOUND)


# =========================
# Authentication endpoints
# =========================


@api.post("/auth/register")
def register() -> tuple[Response, int]:
    data = request.get_json(force=True, silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return error("missing_fields", "MISSING_FIELDS", HTTPStatus.BAD_REQUEST)
    if User.query.filter_by(username=username).first():
        return error("username_taken", "USERNAME_TAKEN", HTTPStatus.CONFLICT)

    u = User(username=username, password_hash=generate_password_hash(password))  # type: ignore
    db.session.add(u)
    db.session.commit()

    return success({"user_id": u.id}, HTTPStatus.CREATED)


@api.post("/auth/login")
def login() -> tuple[Response, int]:
    data = request.get_json(force=True, silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    user = User.query.filter_by(username=username).first()

    if not user or not check_password_hash(user.password_hash, password):
        return error(
            "invalid_credentials",
            "INVALID_CREDENTIALS",
            HTTPStatus.UNAUTHORIZED,
        )

    login_user(user)

    return success({"user": {"id": user.id, "username": user.username}})


@api.get("/auth/logout")
@login_required
def logout() -> tuple[Response, int]:
    logout_user()
    return success({})


@api.get("/me")
@login_required
def me() -> tuple[Response, int]:
    return success({"id": current_user.id, "username": current_user.username})


# ===============
# Chat endpoints
# ===============


@api.post("/chat/create")
@login_required
def create_session() -> tuple[Response, int]:
    data = request.get_json(force=True, silent=True) or {}
    try:
        username = User.query.filter_by(
            username=(data.get("with") or "").strip()
        ).first()

        if not username or username.id == current_user.id:
            return error("invalid_user", "INVALID_USER", HTTPStatus.BAD_REQUEST)

        # Normalize pair to satisfy constraint user_a_id < user_b_id
        user_lo, user_hi = sorted((current_user.id, username.id))

        existing = ChatSession.query.filter_by(
            user_a_id=user_lo, user_b_id=user_hi
        ).first()

        if existing:
            return success({"session_id": existing.session_id})

        sid = str(uuid.uuid4())
        s = ChatSession(session_id=sid, user_a_id=user_lo, user_b_id=user_hi)  # type: ignore
        db.session.add(s)
        db.session.commit()

        return success({"session_id": sid}, HTTPStatus.CREATED)
    except Exception as _:
        return error(
            "error_creating_session",
            "ERROR_CREATING_SESSION",
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )


@api.get("/chat/sessions")
@login_required
def list_sessions() -> tuple[Response, int]:
    sessions = (
        ChatSession.query.filter(
            (ChatSession.user_a_id == current_user.id)
            | (ChatSession.user_b_id == current_user.id)
        )
        .order_by(ChatSession.created_at.desc())
        .all()
    )

    out = []
    for s in sessions:
        other_id = (
            s.user_b_id if s.user_a_id == current_user.id else s.user_a_id
        )
        other = db.session.get(User, other_id)
        out.append(
            {
                "session_id": s.session_id,
                "with": {"id": other.id, "username": other.username},  # type: ignore
                "created_at": s.created_at.isoformat(),
            }
        )
    return success({"sessions": out})


@api.get("/chat/<session_id>")
@login_required
def get_messages(session_id: str) -> tuple[Response, int]:
    if not session_id or not is_member(session_id, current_user.id):
        return jsonify({"error": "forbidden"}), 403

    msgs = (
        Message.query.filter_by(session_id=session_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    return success(
        {
            "messages": [
                {
                    "id": m.id,
                    "session_id": m.session_id,
                    "sender_id": m.sender_id,
                    "kind": m.kind,
                    "body": m.body,
                    "created_at": m.created_at.isoformat(),
                }
                for m in msgs
            ]
        }
    )


@api.post("/chat/<session_id>/send")
@login_required
def send_message(session_id: str) -> tuple[Response, int]:
    data = request.get_json(force=True, silent=True) or {}
    message = data.get("message") or ""

    if not session_id or not is_member(session_id, current_user.id):
        return error("forbidden", "FORBIDDEN", HTTPStatus.FORBIDDEN)

    if not isinstance(message, str):
        return error("bad_message", "BAD_MESSAGE", HTTPStatus.BAD_REQUEST)

    message = message.strip()

    if not message:
        return error("empty_message", "EMPTY_MESSAGE", HTTPStatus.BAD_REQUEST)
    if len(message) > 1000:
        return error(
            "message_too_long", "MESSAGE_TOO_LONG", HTTPStatus.BAD_REQUEST
        )

    m = Message(
        session_id=session_id,  # type: ignore
        sender_id=current_user.id,  # type: ignore
        kind="message",  # type: ignore
        body=message,  # type: ignore
    )
    db.session.add(m)
    db.session.commit()

    return success({"message_id": m.id}, HTTPStatus.CREATED)


@api.post("/chat/emoticons")
@login_required
def get_emoticon_asset() -> tuple[Response, int] | Response:
    data = request.get_json(force=True, silent=True) or request.form or {}
    sid = (data.get("session_id") or "").strip()
    filename = (data.get("filename") or "").strip()

    if not sid or not is_member(sid, current_user.id):
        return error("forbidden", "FORBIDDEN", HTTPStatus.FORBIDDEN)

    return send_from_directory(
        current_app.config["EMOTICONS_DIR"], filename, as_attachment=False
    )


@api.post("/chat/event")
@login_required
def msn_event() -> tuple[Response, int]:
    raw = request.get_data(cache=False)
    content_type = request.headers.get("Content-Type", "")

    # Parsing

    parser = MSNSLPParser()
    try:
        ev = parser.parse(raw, content_type)
    except MSNSLPError as e:
        return error(str(e), "PARSE_ERROR", HTTPStatus.BAD_REQUEST)

    call_id = getattr(ev, "call_id", None)
    from_user = getattr(ev, "from_user", None)

    # Validation

    if not call_id:
        return error(
            "missing_call_id", "MISSING_CALL_ID", HTTPStatus.BAD_REQUEST
        )

    if not from_user:
        return error("missing_sender", "MISSING_SENDER", HTTPStatus.BAD_REQUEST)

    chat_session = ChatSession.query.get(call_id)
    if not chat_session:
        return error("unknown_session", "UNKNOWN_SESSION", HTTPStatus.NOT_FOUND)

    sender = User.query.filter_by(username=from_user).first()
    if not sender:
        return error("unknown_sender", "UNKNOWN_SENDER", HTTPStatus.NOT_FOUND)

    if not is_member(call_id, sender.id):
        return error("forbidden", "FORBIDDEN", HTTPStatus.FORBIDDEN)

    # Process event

    if ev.type == "nudge":
        last = (
            Message.query.filter_by(
                session_id=call_id, kind="activity", sender_id=sender.id
            )
            .order_by(Message.created_at.desc())
            .first()
        )
        now = datetime.now(timezone.utc)
        if (
            last
            and (
                now - last.created_at.replace(tzinfo=timezone.utc)
            ).total_seconds()
            < 2.0
        ):
            return error(
                "rate_limited", "RATE_LIMITED", HTTPStatus.TOO_MANY_REQUESTS
            )

        m = Message(
            session_id=call_id,  # type: ignore
            sender_id=sender.id,  # type: ignore
            kind="nudge",  # type: ignore
            body="",  # type: ignore
        )
        db.session.add(m)
        db.session.commit()

        return success(
            {
                "event": "nudge",
                "session_id": call_id,
                "sender": sender.username,
                "stored_message_id": m.id,
                "received_bytes": len(raw),
            }
        )

    if ev.type == "emoticon":
        asset_id = hashlib.sha256(ev.data).hexdigest()[:16]

        if ev.mime == "image/png":
            ext = "png"
        elif ev.mime == "image/gif":
            ext = "gif"
        elif ev.mime == "image/jpeg":
            ext = "jpg"

        filename = f"{asset_id}.{ext}"
        asset_path = current_app.config["EMOTICONS_DIR"] / filename
        if not asset_path.exists():
            with open(asset_path, "wb") as f:
                f.write(ev.data)

        m = Message(
            session_id=call_id,  # type: ignore
            sender_id=sender.id,  # type: ignore
            kind="emoticon",  # type: ignore
            body=filename,  # type: ignore
        )
        db.session.add(m)
        db.session.commit()

        msnobj = ev.msn_object.attrs if ev.msn_object else None

        return success(
            {
                "event": "emoticon",
                "session_id": call_id,
                "sender": sender.username,
                "stored_message_id": m.id,
                "asset": filename,
                "mime": ev.mime,
                "msn_object": msnobj,
                "received_bytes": len(raw),
            }
        )

    return success(
        {
            "event": "ignored",
            "session_id": call_id,
            "sender": sender.username,
            "received_bytes": len(raw),
        }
    )


# =================
# Export endpoints
# =================


@api.post("/export/chat")
def chat_export() -> tuple[Response, int] | Response:
    data = request.get_json(force=True, silent=True) or {}
    sid = (data.get("session_id") or "").strip()
    fmt = (data.get("format") or "html").strip().lower()

    if not sid:
        return error(
            "missing_session_id", "MISSING_SESSION_ID", HTTPStatus.BAD_REQUEST
        )

    if fmt not in ("xml", "html"):
        return error("bad_format", "BAD_FORMAT", HTTPStatus.BAD_REQUEST)

    if not ChatSession.query.get(sid):
        return error("unknown_session", "UNKNOWN_SESSION", HTTPStatus.NOT_FOUND)

    # NOTE: This endpoint is a temporary WIP used for validating the export
    # rendering logic.

    return success({"data": render_export(sid, fmt)})
