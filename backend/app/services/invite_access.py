import base64
import hashlib
import hmac
import json
import time
from typing import Optional

from fastapi import Depends, HTTPException, Request

from app.config import Settings, get_settings


def normalize_invite_code(code: str) -> str:
    return code.strip().upper()


def invite_code_digest(code: str) -> str:
    return hashlib.sha256(normalize_invite_code(code).encode("utf-8")).hexdigest()


def _configured_invites(settings: Settings) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    for raw_entry in settings.invite_code_hashes.split(","):
        raw_entry = raw_entry.strip()
        if not raw_entry:
            continue
        invite_id, separator, digest = raw_entry.partition(":")
        invite_id = invite_id.strip()
        digest = digest.strip().lower()
        if not separator or not invite_id or len(digest) != 64:
            continue
        try:
            int(digest, 16)
        except ValueError:
            continue
        entries.append((invite_id, digest))
    return entries


def _configured_values(raw_values: str) -> set[str]:
    return {value.strip().lower() for value in raw_values.split(",") if value.strip()}


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _token_secret(settings: Settings) -> bytes:
    secret = settings.invite_token_secret.encode("utf-8")
    if len(secret) < 32:
        raise HTTPException(status_code=503, detail="Invite access is not configured.")
    return secret


def redeem_invite_code(code: str, settings: Settings, now: Optional[int] = None) -> tuple[str, str]:
    configured = _configured_invites(settings)
    if not configured:
        raise HTTPException(status_code=503, detail="Invite access is not configured.")

    candidate = invite_code_digest(code)
    if candidate in _configured_values(settings.invite_revoked_code_hashes):
        raise HTTPException(status_code=401, detail="That invite code is not valid.")

    invite_id = ""
    for configured_id, configured_digest in configured:
        if hmac.compare_digest(candidate, configured_digest):
            invite_id = configured_id
    if not invite_id:
        raise HTTPException(status_code=401, detail="That invite code is not valid.")

    issued_at = int(time.time()) if now is None else int(now)
    payload = {
        "exp": issued_at + settings.invite_token_ttl_seconds,
        "iat": issued_at,
        "sub": invite_id,
        "v": 1,
    }
    encoded_payload = _b64encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signature = hmac.new(_token_secret(settings), encoded_payload.encode("ascii"), hashlib.sha256).digest()
    return f"{encoded_payload}.{_b64encode(signature)}", invite_id


def verify_invite_token(token: str, settings: Settings, now: Optional[int] = None) -> str:
    try:
        encoded_payload, encoded_signature = token.split(".", 1)
        supplied_signature = _b64decode(encoded_signature)
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invite access has expired or is invalid.")

    expected_signature = hmac.new(
        _token_secret(settings), encoded_payload.encode("ascii"), hashlib.sha256
    ).digest()
    if not hmac.compare_digest(supplied_signature, expected_signature):
        raise HTTPException(status_code=401, detail="Invite access has expired or is invalid.")

    try:
        payload = json.loads(_b64decode(encoded_payload))
        invite_id = str(payload["sub"])
        expires_at = int(payload["exp"])
        version = int(payload["v"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        raise HTTPException(status_code=401, detail="Invite access has expired or is invalid.")

    current_time = int(time.time()) if now is None else int(now)
    revoked_ids = _configured_values(settings.invite_revoked_ids)
    if version != 1 or not invite_id or invite_id.lower() in revoked_ids or expires_at <= current_time:
        raise HTTPException(status_code=401, detail="Invite access has expired or is invalid.")
    return invite_id


def require_invite_access(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> Optional[str]:
    if not settings.invite_enforcement_enabled:
        return None
    authorization = request.headers.get("Authorization", "")
    scheme, separator, token = authorization.partition(" ")
    if not separator or scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="Enter your BiteLog invite code to continue.")
    return verify_invite_token(token.strip(), settings)
