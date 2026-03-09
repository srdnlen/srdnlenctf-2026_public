import os
import secrets
import string
from datetime import datetime, timezone
from html import escape

from models import ChatSession, Message, User, db
from werkzeug.security import generate_password_hash

# ===================
# Database utilities
# ===================


def init_db() -> None:
    if User.query.count() > 0:
        return

    user1 = User(
        username="justlel",  # type: ignore
        password_hash=generate_password_hash(  # type: ignore
            "".join(
                secrets.choice(string.ascii_uppercase + string.digits)
                for _ in range(16)
            )
        ),
    )
    user2 = User(
        username="darkknight",  # type: ignore
        password_hash=generate_password_hash(  # type: ignore
            "".join(
                secrets.choice(string.ascii_uppercase + string.digits)
                for _ in range(16)
            )
        ),
    )
    user3 = User(
        username="pysu",  # type: ignore
        password_hash=generate_password_hash(  # type: ignore
            "".join(
                secrets.choice(string.ascii_uppercase + string.digits)
                for _ in range(16)
            )
        ),
    )
    user4 = User(
        username="uNickz",  # type: ignore
        password_hash=generate_password_hash(  # type: ignore
            "".join(
                secrets.choice(string.ascii_uppercase + string.digits)
                for _ in range(16)
            )
        ),
    )

    db.session.add_all([user1, user2, user3, user4])
    db.session.commit()

    session_id = "00000000-0000-0000-0000-000000000000"
    s = ChatSession(
        session_id=session_id,  # type: ignore
        user_a_id=user1.id,  # type: ignore
        user_b_id=user2.id,  # type: ignore
    )
    db.session.add(s)
    db.session.commit()

    flag = os.environ.get("FLAG", "srdnlen{REDACTED}")
    msgs = [
        Message(
            session_id=session_id,  # type: ignore
            sender_id=user1.id,  # type: ignore
            kind="message",  # type: ignore
            body="Hi Chri, I've finished setting up the team's infrastructure.",  # type: ignore
        ),
        Message(
            session_id=session_id,  # type: ignore
            sender_id=user2.id,  # type: ignore
            kind="message",  # type: ignore
            body="We Lo, thanks! I'll take a look at them as soon as I can.",  # type: ignore
        ),
        Message(
            session_id=session_id,  # type: ignore
            sender_id=user1.id,  # type: ignore
            kind="message",  # type: ignore
            body=f"Perfect, I'll send you the password here. {flag}",  # type: ignore
        ),
    ]
    db.session.add_all(msgs)
    db.session.commit()


# ====================
# Chat utilities
# ====================


def is_member(session_id: str, user_id: int) -> bool:
    s = ChatSession.query.get(session_id)
    if not s:
        return False
    return (s.user_a_id == user_id) or (s.user_b_id == user_id)


# ====================
# Rendering utilities
# ====================


def render_export(session_id: str, export_fmt: str) -> str:
    msgs = (
        Message.query.filter_by(session_id=session_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    if export_fmt == "xml":
        blob = _render_export_xml(msgs, session_id)
    else:
        blob = _render_export_html(msgs, session_id)

    return blob


def _render_export_xml(messages: list[Message], session_id: str) -> str:
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append(f'<chatlog session_id="{escape(session_id)}">')
    lines.append(
        f'  <meta generated_at="{escape(datetime.now(timezone.utc).isoformat())}"/>'
    )

    for m in messages:
        body = escape(m.body)
        ts = escape(m.created_at.isoformat())
        lines.append(
            f'  <message id="{m.id}" kind="{escape(m.kind)}" sender_id="{m.sender_id}" ts="{ts}">{body}</message>'
        )

    lines.append("</chatlog>")
    return "\n".join(lines)


def _render_export_html(messages: list[Message], session_id: str) -> str:
    rows = []
    for m in messages:
        rows.append(
            f"<tr><td>{escape(m.created_at.isoformat())}</td>"
            f"<td>{escape(m.kind)}</td>"
            f"<td>{m.sender_id}</td>"
            f"<td>{escape(m.body)}</td></tr>"
        )

    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>MSN Chat Export</title>
</head>
<body>
  <h1>Chat Export</h1>
  <p><b>session_id</b>: {escape(session_id)}</p>
  <p><b>generated_at</b>: {escape(datetime.now(timezone.utc).isoformat())}</p>
  <h3>Meta</h3>
  <h3>Messages</h3>
  <table border="1" cellpadding="6" cellspacing="0">
    <tr><th>ts</th><th>kind</th><th>sender_id</th><th>body</th></tr>
    {"".join(rows)}
  </table>
</body>
</html>
"""
    return html
