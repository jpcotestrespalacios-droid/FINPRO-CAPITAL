from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from typing import Optional

from supabase_db import get_sb
from config import settings

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def crear_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
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


class UsuarioCreate(BaseModel):
    email: str
    nombre: str
    nit: str
    telefono: Optional[str] = None
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


@router.post("/registro", summary="Registrar nueva empresa")
async def registrar(usuario: UsuarioCreate):
    sb = get_sb()
    existing = sb.table("usuarios").select("id").eq("email", usuario.email).execute()
    if existing.data:
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
async def login(form: OAuth2PasswordRequestForm = Depends()):
    sb = get_sb()
    result = sb.table("usuarios").select("*").eq("email", form.username).execute()
    if not result.data:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    usuario = result.data[0]
    if not verify_password(form.password, usuario["hashed_password"]):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    token = crear_token({"sub": usuario["email"], "nit": usuario["nit"]})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", summary="Datos del usuario actual")
async def me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "nombre": current_user["nombre"],
        "nit": current_user["nit"],
        "telefono": current_user.get("telefono"),
    }
