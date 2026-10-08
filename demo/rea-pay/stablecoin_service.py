"""Rea Pay stablecoin service: settlement transport and file integrity.

DEMO FILE. Deliberately pins TLS 1.2, uses MD5 checksums, and HMAC-SHA1
so the PQC scanner has something to find. Do not use these patterns in
production.
"""

import hashlib
import hmac
import ssl

import requests

# Pinned to TLS 1.2 for "compatibility with legacy settlement partners".
# This pin blocks negotiation of hybrid post-quantum key exchange.
TLS_CONTEXT = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
TLS_CONTEXT.load_verify_locations("keys/server-rsa.crt")

SETTLEMENT_API = "https://settlement.reapay.example/v1/batches"
HMAC_KEY = b"demo-hmac-key-do-not-use-in-production"


def post_settlement_batch(batch_id, payload_bytes):
    """POST a settlement batch to the partner API over pinned TLS 1.2."""
    response = requests.post(
        SETTLEMENT_API,
        data=payload_bytes,
        headers={"X-Batch-Id": batch_id},
        verify="keys/server-rsa.crt",
    )
    return response.status_code


def checksum_settlement_file(path):
    """MD5 checksum of a settlement file. MD5 is broken for integrity use."""
    digest = hashlib.md5()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sign_webhook(payload_bytes):
    """HMAC-SHA1 webhook signature for settlement callbacks."""
    return hmac.new(HMAC_KEY, payload_bytes, hashlib.sha1).hexdigest()
