"""轻量级用户认证：密码哈希 + JWT。

Phase 4 MVP：仅做注册/登录/JWT，没接入 OAuth 与 RBAC。
生产环境建议改用 Authlib + Keycloak / 自托管 OAuth。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any

from app.config import settings


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return f"pbkdf2_sha256$200000${base64.b64encode(salt).decode()}${base64.b64encode(h).decode()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algo, iters, salt_b64, hash_b64 = encoded.split("$")
        if algo != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64)
        h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(iters))
        return hmac.compare_digest(base64.b64encode(h).decode(), hash_b64)
    except Exception:
        return False


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    s += "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s)


def create_jwt(payload: dict[str, Any], expires_in: int = 7 * 24 * 3600) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    body = {**payload, "iat": int(time.time()), "exp": int(time.time()) + expires_in}
    seg1 = _b64url(json.dumps(header, separators=(",", ":")).encode())
    seg2 = _b64url(json.dumps(body, separators=(",", ":")).encode())
    msg = f"{seg1}.{seg2}".encode()
    sig = hmac.new(settings.app_secret_key.encode(), msg, hashlib.sha256).digest()
    return f"{seg1}.{seg2}.{_b64url(sig)}"


def decode_jwt(token: str) -> dict | None:
    try:
        seg1, seg2, seg3 = token.split(".")
        msg = f"{seg1}.{seg2}".encode()
        expected = hmac.new(settings.app_secret_key.encode(), msg, hashlib.sha256).digest()
        if not hmac.compare_digest(_b64url_decode(seg3), expected):
            return None
        body = json.loads(_b64url_decode(seg2))
        if body.get("exp", 0) < int(time.time()):
            return None
        return body
    except Exception:
        return None
