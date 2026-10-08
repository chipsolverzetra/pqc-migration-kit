"""Rea Pay custody service: key wrapping and token issuance.

DEMO FILE. Deliberately uses RSA-2048 for key wrapping and RS256 for JWTs
so the PQC scanner has something to find. Do not use these patterns in
production.
"""

import datetime

import jwt
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA

# RSA-2048 wrapping key. Generated at deploy time and never rotated.
# TODO: move key storage to the pkcs11 HSM before the next audit.
WRAPPING_KEY = RSA.generate(2048)
PUBLIC_WRAPPING_KEY = WRAPPING_KEY.publickey()

# JWT signing key, also RSA-2048. Tokens are valid for 30 days, which means
# a forged token remains useful long after issuance.
JWT_SIGNING_KEY_PEM = WRAPPING_KEY.export_key().decode("utf-8")
JWT_ALGORITHM = "RS256"
TOKEN_TTL_DAYS = 30


def wrap_data_key(data_key_bytes):
    """Wrap a per-customer data key with the RSA-2048 wrapping key."""
    cipher = PKCS1_OAEP.new(PUBLIC_WRAPPING_KEY)
    return cipher.encrypt(data_key_bytes)


def unwrap_data_key(wrapped_bytes):
    """Unwrap a per-customer data key."""
    cipher = PKCS1_OAEP.new(WRAPPING_KEY)
    return cipher.decrypt(wrapped_bytes)


def issue_custody_token(customer_id, vault_id):
    """Issue a JWT granting custody API access for a customer vault."""
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": customer_id,
        "vault": vault_id,
        "iat": now,
        "exp": now + datetime.timedelta(days=TOKEN_TTL_DAYS),
    }
    # RS256: an RSA signature a quantum adversary can forge once the public
    # key is known. The public key is published in our JWKS endpoint.
    return jwt.encode(payload, JWT_SIGNING_KEY_PEM, algorithm=JWT_ALGORITHM)


def verify_custody_token(token):
    """Verify a custody JWT."""
    public_pem = PUBLIC_WRAPPING_KEY.export_key().decode("utf-8")
    return jwt.decode(token, public_pem, algorithms=[JWT_ALGORITHM])
