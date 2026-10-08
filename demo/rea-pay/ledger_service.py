"""Rea Pay ledger service: transaction signing.

DEMO FILE. Deliberately uses classical elliptic curve cryptography
(ECDSA over secp256k1) so the PQC scanner has something to find.
Do not use these patterns in production.
"""

import hashlib
import json

import ecdsa
from ecdsa import SigningKey, VerifyingKey, SECP256k1

# The curve is hardcoded in two places: the import above and the string below.
# Both must change when we migrate signing to ML-DSA (FIPS 204).
SIGNING_CURVE_NAME = "secp256k1"
CURVE = SECP256k1


class LedgerSigner:
    """Signs Rea Pay ledger transactions with ECDSA/secp256k1."""

    def __init__(self):
        # Key generation pinned to the secp256k1 curve.
        self.signing_key = SigningKey.generate(curve=CURVE)
        self.verifying_key = self.signing_key.get_verifying_key()

    def sign_transaction(self, sender, recipient, amount_cents):
        """Sign a transaction payload and return the signature bytes."""
        payload = json.dumps({
            "sender": sender,
            "recipient": recipient,
            "amount_cents": amount_cents,
        }, sort_keys=True).encode("utf-8")
        digest = hashlib.sha256(payload).digest()
        # ECDSA signatures over secp256k1: forgeable by a quantum adversary
        # running Shor's algorithm once the verifying key is public, which it
        # is, because every transaction carries it.
        return self.signing_key.sign_digest(digest)

    def verify_transaction(self, signature, payload, verifying_key_bytes):
        """Verify a transaction signature against a verifying key."""
        verifying_key = VerifyingKey.from_string(verifying_key_bytes, curve=SECP256k1)
        digest = hashlib.sha256(payload).digest()
        return verifying_key.verify_digest(signature, digest)


def address_from_verifying_key(verifying_key):
    """Derive a Rea Pay address from a verifying key (toy scheme)."""
    raw = verifying_key.to_string()
    return "rp1" + hashlib.sha256(raw).hexdigest()[:32]
