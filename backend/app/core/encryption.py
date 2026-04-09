import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# In a real production system, this key should come from an environment variable (e.g., from settings)
# Example: AESGCM.generate_key(bit_length=256)
# For the sake of standardizing during development without crashing, check env
_ENCRYPTION_KEY_B64 = os.environ.get("OMNI_MEMORY_KEY")

if not _ENCRYPTION_KEY_B64:
    # Generate a dev key and keep it in memory. 
    # Warning: Sessions will become unreadable upon server restart if the key isn't persisted!
    import warnings
    warnings.warn("OMNI_MEMORY_KEY not present in environment. Generating a volatile key for development. Encrypted data will be lost on restart.")
    default_key = AESGCM.generate_key(bit_length=256)
    _ENCRYPTION_KEY_B64 = base64.b64encode(default_key).decode('utf-8')
    os.environ["OMNI_MEMORY_KEY"] = _ENCRYPTION_KEY_B64


def _get_key() -> bytes:
    key_b64 = os.environ.get("OMNI_MEMORY_KEY", _ENCRYPTION_KEY_B64)
    return base64.b64decode(key_b64)

def encrypt_string(data: str) -> str:
    """Encrypts a string using AES-GCM and returns a base64 encoded token containing the nonce and ciphertext."""
    if not data:
        return data
        
    aesgcm = AESGCM(_get_key())
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, data.encode('utf-8'), None)
    
    # Store nonce + ciphertext together
    token = nonce + ciphertext
    return base64.b64encode(token).decode('utf-8')

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
        return plaintext.decode('utf-8')
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to decrypt string: {e}")
        return "<Decryption Failed>"
