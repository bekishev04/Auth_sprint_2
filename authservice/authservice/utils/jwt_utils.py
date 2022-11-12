import base64
import hashlib
import hmac
import json
from typing import Optional

from ..config import cfg

secret = cfg.JWT_SECRET


def get_jwt_token(payload: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64_str = base64.urlsafe_b64encode(
        json.dumps(header).encode()
    ).decode()
    payload_b64_str = base64.urlsafe_b64encode(payload.encode()).decode()

    body = f"{header_b64_str}.{payload_b64_str}"
    signature = hmac.new(
        secret.encode(), body.encode(), hashlib.sha256
    ).hexdigest()
    return f"{header_b64_str}.{payload_b64_str}.{signature}"


def decode_jwt_token(token: str) -> Optional[str]:
    if check_jwt_token(token):
        return base64.urlsafe_b64decode(token.split(".")[1]).decode("utf-8")
    return None


def check_jwt_token(token: str) -> bool:
    try:
        _, body, signature = token.split(".")
        body_str = base64.urlsafe_b64decode(body).decode("utf-8")
    except ValueError:
        # todo log error
        return False
    t = get_jwt_token(body_str)
    if t.split(".")[-1] == signature:
        return True
    return False
