"""
AES-GCM 256-bit encryption for Omni-Memory deep privacy.

Encrypts/decrypts strings using a 32-byte key from OMNI_MEMORY_KEY.
If the key is not set, generates a volatile dev key (data lost on restart).
"""

import base64
import os
import warnings

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _resolve_encryption_key() -> str:
    """
    Resolve the encryption key from environment.
    Uses OMNI_MEMORY_KEY from .env. If missing, generates a volatile key for development.
    """
    key_b64 = os.environ.get("OMNI_MEMORY_KEY", "")

    if not key_b64:
        warnings.warn(
            "⚠️ OMNI_MEMORY_KEY not present in environment. "
            "Generating a volatile key for development. "
            "Encrypted data will be LOST on restart! "
            "Generate a stable key: python -c \"import os,base64; print(base64.b64encode(os.urandom(32)).decode())\"",
            stacklevel=2,
        )
        default_key = AESGCM.generate_key(bit_length=256)
        key_b64 = base64.b64encode(default_key).decode("utf-8")
        os.environ["OMNI_MEMORY_KEY"] = key_b64

    return key_b64


# Resolve once at module load
_ENCRYPTION_KEY_B64 = _resolve_encryption_key()


def _get_key() -> bytes:
    return base64.b64decode(_ENCRYPTION_KEY_B64)


def encrypt_string(data: str) -> str:
    """Encrypts a string using AES-GCM and returns a base64 encoded token containing the nonce and ciphertext."""
    if not data:
        return data

    aesgcm = AESGCM(_get_key())
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, data.encode("utf-8"), None)

    # Store nonce + ciphertext together
    token = nonce + ciphertext
    return base64.b64encode(token).decode("utf-8")


def decrypt_string(token: str) -> str:
    """Decrypts a base64 encoded token from encrypt_string."""
    if not token:
        return token

    try:
        raw_data = base64.b64decode(token)
        nonce = raw_data[:12]
        ciphertext = raw_data[12:]

        aesgcm = AESGCM(_get_key())
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to decrypt string: {e}")
        return "<Decryption Failed>"
