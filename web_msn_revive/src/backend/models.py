from datetime import datetime, timezone

from app import db
from flask_login import UserMixin


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)


class ChatSession(db.Model):
    __tablename__ = "chat_sessions"
    __table_args__ = (
        db.UniqueConstraint(
            "user_a_id", "user_b_id", name="uq_chat_sessions_pair"
        ),
        db.CheckConstraint(
            "user_a_id < user_b_id", name="ck_chat_sessions_order"
        ),
    )
    session_id = db.Column(db.String(64), primary_key=True)
    user_a_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    user_b_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)


class Message(db.Model):
    __tablename__ = "messages"
    __table_args__ = (
        db.CheckConstraint(
            "kind IN ('message', 'nudge', 'emoticon')",
            name="ck_messages_kind_valid",
        ),
    )
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(
        db.String(64),
        db.ForeignKey("chat_sessions.session_id"),
        nullable=False,
        index=True,
    )
    sender_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    body = db.Column(db.Text, nullable=False)
    kind = db.Column(db.String(24), default="message", nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)


class Export(db.Model):
    __tablename__ = "exports"
    __table_args__ = (
        db.CheckConstraint(
            "fmt IN ('xml', 'html')", name="ck_exports_fmt_valid"
        ),
    )
    export_id = db.Column(db.String(64), primary_key=True)
    owner_user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    session_id = db.Column(
        db.String(64),
        db.ForeignKey("chat_sessions.session_id"),
        nullable=False,
        index=True,
    )
    fmt = db.Column(db.String(16), nullable=False)
    path = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
