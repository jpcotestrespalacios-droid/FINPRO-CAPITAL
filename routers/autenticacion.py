"""
routers/autenticacion.py
Autenticación segura para fintech colombiana:
  - httpOnly cookies (JWT nunca expuesto en JS → protección XSS)
  - Cookie CSRF legible por JS (double-submit cookie pattern)
  - Rate limiting en login/registro (5 intentos / 60s por IP)
  - get_current_user lee cookie primero, Bearer token como fallback
    (mantiene compatibilidad con API Explorer y clientes externos)
  - POST /logout expira ambas cookies
"""
import os
import secrets
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel

from supabase_db import get_sb
from config import settings

router = APIRouter()

# auto_error=False → no lanza 401 automáticamente si no hay header;
# get_current_user decide si usar cookie o Bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── COOKIE CONFIG ──────────────────────────────────────────────────────────────
COOKIE_SESSION = "radian_session"   # httpOnly — contiene el JWT
COOKIE_CSRF    = "radian_csrf"      # legible por JS — double-submit CSRF
COOKIE_MAX_AGE = 3600               # 1 hora

# En Vercel: VERCEL=1 → secure=True (HTTPS).
# En tests/localhost: sin env var → secure=False para que TestClient funcione.
_IS_SECURE = bool(os.getenv("VERCEL") or os.getenv("SECURE_COOKIES"))


def _set_auth_cookies(response: Response, token: str) -> str:
    """Setea JWT en httpOnly cookie y CSRF token en cookie legible por JS.
    Retorna el CSRF token generado."""
    csrf_token = secrets.token_hex(32)

    response.set_cookie(
        key=COOKIE_SESSION,
        value=token,
        httponly=True,           # JS NO puede leerla → protección XSS
        secure=_IS_SECURE,
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
        path="/",
    )
    response.set_cookie(
        key=COOKIE_CSRF,
        value=csrf_token,
        httponly=False,          # JS DEBE poder leerla (double-submit)
        secure=_IS_SECURE,
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
        path="/",
    )
    return csrf_token


def _clear_auth_cookies(response: Response) -> None:
    """Expira/elimina ambas cookies al hacer logout."""
    response.delete_cookie(key=COOKIE_SESSION, path="/", samesite="lax")
    response.delete_cookie(key=COOKIE_CSRF,    path="/", samesite="lax")


# ── RATE LIMITING ──────────────────────────────────────────────────────────────
# In-memory: funciona en instancia única. En Vercel serverless es best-effort.
# Para rate limiting estricto en producción escalar a Redis/Upstash.
_attempts: dict = defaultdict(list)


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_rate_limit(ip: str, max_attempts: int = 5, window: int = 60) -> bool:
    """Retorna True si puede continuar, False si superó el límite."""
    now = time.time()
    _attempts[ip] = [t for t in _attempts[ip] if now - t < window]
    if len(_attempts[ip]) >= max_attempts:
        return False
    _attempts[ip].append(now)
    return True


# ── CSRF VALIDATION ────────────────────────────────────────────────────────────
def verify_csrf(request: Request) -> None:
    """
    Valida CSRF para requests mutantes autenticados con cookie.
    Reglas:
      - GET/HEAD/OPTIONS → exento
      - Authorization: Bearer → exento (cliente externo / API Explorer)
      - Sin radian_session cookie → sin sesión activa, no aplica
      - Con cookie pero sin X-CSRF-Token → 403
      - Con cookie y X-CSRF-Token que no coincide con radian_csrf → 403
    """
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return
    if request.headers.get("Authorization", "").startswith("Bearer "):
        return
    if not request.cookies.get(COOKIE_SESSION):
        return  # Sin sesión por cookie, get_current_user manejará el 401

    csrf_header = request.headers.get("X-CSRF-Token", "")
    csrf_cookie = request.cookies.get(COOKIE_CSRF, "")

    if not csrf_header:
        raise HTTPException(status_code=403, detail="CSRF token requerido")
    if not csrf_cookie:
        raise HTTPException(status_code=403, detail="Sesión inválida: falta cookie CSRF")
    if not secrets.compare_digest(csrf_header, csrf_cookie):
        raise HTTPException(status_code=403, detail="CSRF token inválido")


# ── PASSWORD HELPERS ───────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def crear_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# ── get_current_user: cookie primero, Bearer como fallback ────────────────────
def get_current_user(
    request: Request,
    bearer_token: Optional[str] = Depends(oauth2_scheme),
) -> dict:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    # 1. httpOnly cookie (navegador con sesión activa)
    token = request.cookies.get(COOKIE_SESSION)
    # 2. Bearer header (API Explorer, Postman, curl, clientes externos)
    if not token:
        token = bearer_token
    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = get_sb().table("usuarios").select("*").eq("email", email).eq("activo", True).execute()
    if not result.data:
        raise credentials_exception
    return result.data[0]


# ── MODELOS ────────────────────────────────────────────────────────────────────
class UsuarioCreate(BaseModel):
    email: str
    nombre: str
    nit: str
    telefono: Optional[str] = None
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


# ── ENDPOINTS ──────────────────────────────────────────────────────────────────
@router.post("/registro", summary="Registrar nueva empresa")
async def registrar(usuario: UsuarioCreate, request: Request):
    ip = _get_client_ip(request)
    if not _check_rate_limit(ip, max_attempts=10, window=300):
        raise HTTPException(
            status_code=429,
            detail="Demasiados intentos de registro. Espera 5 minutos.",
            headers={"Retry-After": "300"},
        )
    sb = get_sb()
    if sb.table("usuarios").select("id").eq("email", usuario.email).execute().data:
        raise HTTPException(status_code=400, detail="Email ya registrado")
    sb.table("usuarios").insert({
        "email": usuario.email,
        "nombre": usuario.nombre,
        "nit": usuario.nit,
        "telefono": usuario.telefono,
        "hashed_password": hash_password(usuario.password),
        "activo": True,
    }).execute()
    return {"mensaje": "Usuario registrado exitosamente", "email": usuario.email}


@router.post("/token", response_model=Token, summary="Obtener token JWT")
async def login(
    request: Request,
    response: Response,
    form: OAuth2PasswordRequestForm = Depends(),
):
    ip = _get_client_ip(request)
    if not _check_rate_limit(ip, max_attempts=5, window=60):
        raise HTTPException(
            status_code=429,
            detail="Demasiados intentos de inicio de sesión. Espera 1 minuto.",
            headers={"Retry-After": "60"},
        )
    sb = get_sb()
    result = sb.table("usuarios").select("*").eq("email", form.username).execute()
    if not result.data:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    usuario = result.data[0]
    if not verify_password(form.password, usuario["hashed_password"]):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    token = crear_token({"sub": usuario["email"], "nit": usuario["nit"]})
    _set_auth_cookies(response, token)

    # Token también en body para compatibilidad con API Explorer / clientes externos
    return {"access_token": token, "token_type": "bearer"}


@router.post("/logout", summary="Cerrar sesión — expira cookies")
async def logout(response: Response):
    _clear_auth_cookies(response)
    return {"mensaje": "Sesión cerrada exitosamente"}


@router.get("/me", summary="Datos del usuario actual")
async def me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "nombre": current_user["nombre"],
        "nit": current_user["nit"],
        "telefono": current_user.get("telefono"),
    }
