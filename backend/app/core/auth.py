import os
import hashlib
import json
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from hkdf import Hkdf
from jwcrypto import jwe

from app.database import get_db
from app.models.user import User

bearer_scheme = HTTPBearer()

def get_auth_secret() -> str:
    """Return the NextAuth secret from .env."""
    return os.getenv("AUTH_SECRET", "")

def derive_nextauth_key(secret: str, info: str = "Auth.js Generated Encryption Key (authjs.session-token)") -> bytes:
    """
    Derives the AES-GCM-256 encryption key using HKDF as per NextAuth.js / Auth.js specifications.
    Auth.js v5 defaults to: `Auth.js Generated Encryption Key (${cookieName})`
    """
    hkdf = Hkdf(salt=b"", input_key_material=secret.encode("utf-8"), hash=hashlib.sha256)
    return hkdf.expand(info=info.encode("utf-8"), length=32)

def decode_nextauth_jwe(token: str) -> dict:
    """Decodes NextAuth.js encrypted JWE session token securely."""
    secret = get_auth_secret()
    if not secret:
        raise HTTPException(status_code=500, detail="AUTH_SECRET is not configured on the backend.")

    # Try common auth.js info strings depending on if it's beta or release
    infos = [
        "Auth.js Generated Encryption Key (authjs.session-token)",
        "Auth.js Generated Encryption Key (__Secure-authjs.session-token)",
        "NextAuth.js Generated Encryption Key",
        "Auth.js Generated Encryption Key"
    ]
    
    last_error = None
    for info in infos:
        try:
            key_bytes = derive_nextauth_key(secret, info)
            
            # Create a JWK (JSON Web Key) from the derived bytes
            jwk_key = {"k": key_bytes, "kty": "oct"}
            from jwcrypto import jwk
            key = jwk.JWK(**jwk_key)
            
            jwe_token = jwe.JWE()
            jwe_token.deserialize(token)
            jwe_token.decrypt(key)
            payload = json.loads(jwe_token.payload.decode("utf-8"))
            
            # Validate expiration if present
            if "exp" in payload:
                exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
                if datetime.now(timezone.utc) > exp:
                    raise HTTPException(status_code=401, detail="Token has expired.")
            
            return payload
        except Exception as e:
            last_error = e
            continue
            
    # If all decrypt attempts fail
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"Could not validate NextAuth credentials. {last_error}",
        headers={"WWW-Authenticate": "Bearer"},
    )

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    FastAPI Dependency to enforce valid NextAuth session tokens flexibly.
    Checks Cookies (__Secure-authjs.session-token or authjs.session-token) OR Bearer headers.
    """
    token = None
    
    # Try cookies first (Browser fetch with credentials: 'include')
    token = request.cookies.get("authjs.session-token") or request.cookies.get("__Secure-authjs.session-token")
    
    # Try Authorization Header (for Postman/external clients)
    if not token and "Authorization" in request.headers:
        auth_header = request.headers["Authorization"]
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required. No session token found.")

    payload = decode_nextauth_jwe(token)
    
    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token payload: missing email.")
    
    # Retrieve or create User async
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user:
        name = payload.get("name", "")
        picture = payload.get("picture", "")
        user = User(email=email, name=name, picture=picture)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
    return user
