import hashlib
import hmac

from app.webhook_security import verify_signature


def test_verify_signature_success():
    secret = "supersecret"
    payload = b'{"hello":"world"}'
    digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    header = f"sha256={digest}"
    assert verify_signature(payload, secret, header) is True


def test_verify_signature_failure():
    secret = "supersecret"
    payload = b'{"hello":"world"}'
    bad_header = "sha256=badsignature"
    assert verify_signature(payload, secret, bad_header) is False
