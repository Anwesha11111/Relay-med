"""
Encryption Service — AES-256-GCM encryption using the Python cryptography library.
Key is derived from SECUREMED_MASTER_KEY env var via PBKDF2-HMAC-SHA256.
"""

import os
import base64
from dataclasses import dataclass
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from backend.config import settings


@dataclass
class EncryptedBlob:
    nonce: bytes
    ciphertext: bytes
    tag: bytes  # GCM tag is appended by AESGCM; stored separately for clarity

    def to_b64_dict(self) -> dict:
        return {
            "nonce": base64.b64encode(self.nonce).decode(),
            "ciphertext": base64.b64encode(self.ciphertext).decode(),
        }

    @classmethod
    def from_b64_dict(cls, d: dict) -> "EncryptedBlob":
        nonce = base64.b64decode(d["nonce"])
        ciphertext = base64.b64decode(d["ciphertext"])
        return cls(nonce=nonce, ciphertext=ciphertext, tag=b"")


class EncryptionService:
    _SALT = b"securemed_static_salt_v1"  # In prod, store per-user salt securely
    _ITERATIONS = 200_000

    def __init__(self):
        self._key = self._derive_key(settings.RELAYMED_MASTER_KEY.encode())
        self._aesgcm = AESGCM(self._key)

    def _derive_key(self, master_key: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self._SALT,
            iterations=self._ITERATIONS,
        )
        return kdf.derive(master_key)

    def encrypt(self, plaintext: bytes) -> EncryptedBlob:
        nonce = os.urandom(12)  # 96-bit nonce for GCM
        # AESGCM.encrypt appends the 16-byte auth tag to ciphertext
        ciphertext_with_tag = self._aesgcm.encrypt(nonce, plaintext, None)
        return EncryptedBlob(nonce=nonce, ciphertext=ciphertext_with_tag, tag=b"")

    def decrypt(self, blob: EncryptedBlob) -> bytes:
        return self._aesgcm.decrypt(blob.nonce, blob.ciphertext, None)

    def encrypt_string(self, text: str) -> EncryptedBlob:
        return self.encrypt(text.encode("utf-8"))

    def decrypt_string(self, blob: EncryptedBlob) -> str:
        return self.decrypt(blob).decode("utf-8")


# Singleton instance
encryption_service = EncryptionService()
