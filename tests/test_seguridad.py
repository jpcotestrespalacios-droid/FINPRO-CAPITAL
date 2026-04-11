"""
tests/test_seguridad.py
Suite de seguridad para FinPro Capital.

Ejecutar:
    pip install pytest httpx
    pytest tests/test_seguridad.py -v

Nota: estas pruebas usan mocks para Supabase y config, de modo que
      pueden correr sin conexión a la base de datos real.
"""
import os
import sys
import pytest

# ── Path setup ─────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Forzar modo no-secure para que las cookies no exijan HTTPS en tests
os.environ.setdefault("SECURE_COOKIES", "")
os.environ.setdefault("SUPABASE_URL",   "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY",   "test-key-only-for-unit-tests")
os.environ.setdefault("SECRET_KEY",     "test-secret-key-for-pytest-only-32chars!")
os.environ.setdefault("ALGORITHM",      "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")

# ── Mock Supabase antes de importar la app ──────────────────────────────────────
from unittest.mock import MagicMock, patch

# Usuario ficticio para tests
_FAKE_USER = {
    "id": "user-test-uuid",
    "email": "test@finpro.co",
    "nombre": "Empresa Test SAS",
    "nit": "900000001-1",
    "hashed_password": "",   # se reemplaza dinámicamente
    "activo": True,
    "telefono": "+57 300 000 0000",
}


def _make_mock_sb(user_exists=True, user_activo=True):
    """Crea un mock de Supabase con respuestas configurables."""
    sb = MagicMock()
    user = {**_FAKE_USER, "activo": user_activo}

    # Encadenar .table().select().eq().execute()
    def _chain(*_, **__):
        m = MagicMock()
        m.execute.return_value = MagicMock(data=[user] if user_exists else [], count=1)
        m.eq.return_value = m
        m.in_.return_value = m
        m.select.return_value = m
        m.insert.return_value = m
        m.update.return_value = m
        m.order.return_value = m
        m.range.return_value = m
        return m

    sb.table.side_effect = _chain
    return sb


# ── Importar app DESPUÉS de configurar mocks ──────────────────────────────────
with patch("supabase_db.get_sb", return_value=_make_mock_sb()):
    from fastapi.testclient import TestClient
    from main import app
    from routers.autenticacion import hash_password, crear_token, COOKIE_SESSION, COOKIE_CSRF

client = TestClient(app, raise_server_exceptions=False)


# ─────────────────────────────────────────────────────────────────────────────
# Helper: obtener token y cookies de un login exitoso
# ─────────────────────────────────────────────────────────────────────────────
def _login(email="test@finpro.co", password="testpass123"):
    hashed = hash_password(password)
    user_with_hash = {**_FAKE_USER, "hashed_password": hashed}

    def _chain_with_user(*_, **__):
        m = MagicMock()
        m.execute.return_value = MagicMock(data=[user_with_hash], count=1)
        m.eq.return_value = m
        m.select.return_value = m
        return m

    sb_mock = MagicMock()
    sb_mock.table.side_effect = _chain_with_user

    with patch("routers.autenticacion.get_sb", return_value=sb_mock):
        r = client.post(
            "/api/v1/auth/token",
            data={"username": email, "password": password},
        )
    return r


# ═══════════════════════════════════════════════════════════════════════════════
# 1. COOKIES: el JWT debe estar en httpOnly cookie, NO en body usable por XSS
# ═══════════════════════════════════════════════════════════════════════════════
class TestCookieSeguridad:

    def test_login_exitoso_retorna_200(self):
        r = _login()
        assert r.status_code == 200, r.text

    def test_token_presente_en_cookie_session(self):
        """La cookie radian_session debe existir tras el login."""
        r = _login()
        assert COOKIE_SESSION in r.cookies, \
            f"Cookie '{COOKIE_SESSION}' ausente. Cookies: {list(r.cookies.keys())}"

    def test_csrf_cookie_presente(self):
        """La cookie radian_csrf debe existir tras el login."""
        r = _login()
        assert COOKIE_CSRF in r.cookies, \
            f"Cookie '{COOKIE_CSRF}' ausente. Cookies: {list(r.cookies.keys())}"

    def test_cookie_session_es_httponly(self):
        """radian_session debe tener flag HttpOnly (no accesible por JS → protección XSS)."""
        r = _login()
        raw = r.headers.get("set-cookie", "")
        # TestClient puede devolver múltiples Set-Cookie; buscar la de sesión
        set_cookies = r.headers.get_list("set-cookie") if hasattr(r.headers, "get_list") \
                      else [v for k, v in r.headers.items() if k.lower() == "set-cookie"]
        session_cookie_header = next(
            (c for c in set_cookies if COOKIE_SESSION in c), ""
        )
        assert "httponly" in session_cookie_header.lower(), \
            f"Flag HttpOnly ausente en cookie de sesión: {session_cookie_header}"

    def test_csrf_cookie_NO_es_httponly(self):
        """radian_csrf NO debe ser httpOnly (JS necesita leerla para double-submit)."""
        r = _login()
        set_cookies = r.headers.get_list("set-cookie") if hasattr(r.headers, "get_list") \
                      else [v for k, v in r.headers.items() if k.lower() == "set-cookie"]
        csrf_cookie_header = next(
            (c for c in set_cookies if COOKIE_CSRF in c and COOKIE_SESSION not in c), ""
        )
        assert "httponly" not in csrf_cookie_header.lower(), \
            f"Cookie CSRF NO debe ser httponly: {csrf_cookie_header}"

    def test_samesite_lax_en_cookie_session(self):
        """radian_session debe tener SameSite=lax."""
        r = _login()
        set_cookies = r.headers.get_list("set-cookie") if hasattr(r.headers, "get_list") \
                      else [v for k, v in r.headers.items() if k.lower() == "set-cookie"]
        session_h = next((c for c in set_cookies if COOKIE_SESSION in c), "")
        assert "samesite=lax" in session_h.lower(), \
            f"SameSite=lax ausente: {session_h}"

    def test_token_en_body_JSON_para_compatibilidad_API_Explorer(self):
        """El token TAMBIÉN aparece en body (compatibilidad Bearer/API Explorer)."""
        r = _login()
        d = r.json()
        assert "access_token" in d
        assert d["token_type"] == "bearer"
        assert len(d["access_token"]) > 20


# ═══════════════════════════════════════════════════════════════════════════════
# 2. LOGOUT: debe expirar las cookies
# ═══════════════════════════════════════════════════════════════════════════════
class TestLogout:

    def test_logout_retorna_200(self):
        r = client.post("/api/v1/auth/logout")
        assert r.status_code == 200

    def test_logout_expira_cookie_session(self):
        """Después del logout, radian_session debe estar vacía o con max-age=0."""
        r = client.post("/api/v1/auth/logout")
        set_cookies = r.headers.get_list("set-cookie") if hasattr(r.headers, "get_list") \
                      else [v for k, v in r.headers.items() if k.lower() == "set-cookie"]
        session_h = next((c for c in set_cookies if COOKIE_SESSION in c), "")
        # Una cookie expirada tiene max-age=0 o expires en el pasado
        cookie_is_cleared = (
            "max-age=0" in session_h.lower()
            or 'expires="thu, 01 jan 1970' in session_h.lower()
            or session_h.split(f"{COOKIE_SESSION}=")[1].split(";")[0].strip() == ""
            if session_h else False
        )
        assert cookie_is_cleared or session_h == "", \
            f"Cookie de sesión no fue expirada correctamente: {session_h}"

    def test_logout_expira_cookie_csrf(self):
        """Después del logout, radian_csrf debe estar vacía o con max-age=0."""
        r = client.post("/api/v1/auth/logout")
        set_cookies = r.headers.get_list("set-cookie") if hasattr(r.headers, "get_list") \
                      else [v for k, v in r.headers.items() if k.lower() == "set-cookie"]
        csrf_h = next(
            (c for c in set_cookies if COOKIE_CSRF in c and COOKIE_SESSION not in c), ""
        )
        cookie_is_cleared = (
            "max-age=0" in csrf_h.lower()
            or csrf_h.split(f"{COOKIE_CSRF}=")[1].split(";")[0].strip() == ""
            if csrf_h else False
        )
        assert cookie_is_cleared or csrf_h == "", \
            f"Cookie CSRF no fue expirada: {csrf_h}"

    def test_logout_mensaje_correcto(self):
        r = client.post("/api/v1/auth/logout")
        assert r.json().get("mensaje") == "Sesión cerrada exitosamente"


# ═══════════════════════════════════════════════════════════════════════════════
# 3. CSRF: endpoints mutantes con cookie deben requerir X-CSRF-Token
# ═══════════════════════════════════════════════════════════════════════════════
class TestCSRF:

    def _get_session_cookie(self):
        r = _login()
        return r.cookies.get(COOKIE_SESSION), r.cookies.get(COOKIE_CSRF)

    def test_post_sin_cookie_sesion_no_requiere_csrf(self):
        """Sin cookie de sesión activa el middleware no aplica CSRF (auth fallará por 401, no 403)."""
        r = client.post(
            "/api/v1/facturas/registrar",
            json={"cufe": "x"},
            # Sin cookies → no hay sesión activa → CSRF no aplica, auth retorna 401
        )
        assert r.status_code != 403, "No debería retornar 403 CSRF sin sesión activa"

    def test_post_con_cookie_sin_csrf_header_retorna_403(self):
        """Con cookie de sesión pero sin X-CSRF-Token debe retornar 403."""
        session, _ = self._get_session_cookie()
        if not session:
            pytest.skip("Login falló — revisar mock de Supabase")

        r = client.post(
            "/api/v1/facturas/registrar",
            json={"cufe": "test"},
            cookies={COOKIE_SESSION: session},
            # Sin X-CSRF-Token
        )
        assert r.status_code == 403, f"Esperado 403, obtenido {r.status_code}: {r.text}"

    def test_post_con_csrf_incorrecto_retorna_403(self):
        """Con cookie de sesión y X-CSRF-Token inválido debe retornar 403."""
        session, _ = self._get_session_cookie()
        if not session:
            pytest.skip("Login falló — revisar mock de Supabase")

        r = client.post(
            "/api/v1/facturas/registrar",
            json={"cufe": "test"},
            cookies={COOKIE_SESSION: session, COOKIE_CSRF: "csrf-valido"},
            headers={"X-CSRF-Token": "csrf-INCORRECTO"},
        )
        assert r.status_code == 403, f"Esperado 403, obtenido {r.status_code}: {r.text}"

    def test_get_sin_csrf_header_es_permitido(self):
        """GET nunca debe requerir CSRF token."""
        r = client.get("/api/v1/facturas/")
        # Puede ser 401 (sin auth) pero nunca 403 por CSRF
        assert r.status_code != 403, "GET no debe requerir CSRF"

    def test_bearer_token_exento_de_csrf(self):
        """Con Authorization: Bearer el middleware CSRF no aplica."""
        token = crear_token({"sub": "test@finpro.co", "nit": "900000001-1"})
        user_mock = MagicMock()
        user_mock.execute.return_value = MagicMock(data=[_FAKE_USER])
        user_mock.eq.return_value = user_mock
        user_mock.select.return_value = user_mock

        sb = MagicMock()
        sb.table.return_value = user_mock

        with patch("routers.autenticacion.get_sb", return_value=sb):
            r = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )
        # 200 o 401 (si el mock no devuelve usuario) pero nunca 403 por CSRF
        assert r.status_code != 403


# ═══════════════════════════════════════════════════════════════════════════════
# 4. RATE LIMITING: máximo 5 intentos de login por IP en 60s
# ═══════════════════════════════════════════════════════════════════════════════
class TestRateLimit:

    def test_exceder_intentos_login_retorna_429(self):
        """Más de 5 intentos fallidos de login en 60s → 429."""
        from routers.autenticacion import _attempts
        # Limpiar intentos previos del IP de test
        _attempts.clear()

        sb = MagicMock()
        no_user = MagicMock()
        no_user.execute.return_value = MagicMock(data=[])
        no_user.eq.return_value = no_user
        no_user.select.return_value = no_user
        sb.table.return_value = no_user

        last_r = None
        with patch("routers.autenticacion.get_sb", return_value=sb):
            for i in range(7):  # 2 más del límite
                last_r = client.post(
                    "/api/v1/auth/token",
                    data={"username": f"attack{i}@x.co", "password": "wrong"},
                )

        assert last_r is not None
        assert last_r.status_code == 429, \
            f"Esperado 429 después de 6+ intentos, obtenido {last_r.status_code}"
        assert "Retry-After" in last_r.headers

    def test_retry_after_header_presente_en_429(self):
        """El header Retry-After debe estar presente en respuesta 429."""
        from routers.autenticacion import _attempts
        _attempts.clear()

        sb = MagicMock()
        no_user = MagicMock()
        no_user.execute.return_value = MagicMock(data=[])
        no_user.eq.return_value = no_user
        no_user.select.return_value = no_user
        sb.table.return_value = no_user

        with patch("routers.autenticacion.get_sb", return_value=sb):
            for _ in range(6):
                r = client.post(
                    "/api/v1/auth/token",
                    data={"username": "brute@x.co", "password": "wrong"},
                )

        assert r.status_code == 429
        assert r.headers.get("Retry-After") == "60"


# ═══════════════════════════════════════════════════════════════════════════════
# 5. CREDENTIALS INCORRECTAS
# ═══════════════════════════════════════════════════════════════════════════════
class TestCredenciales:

    def test_usuario_inexistente_retorna_401(self):
        sb = MagicMock()
        empty = MagicMock()
        empty.execute.return_value = MagicMock(data=[])
        empty.eq.return_value = empty
        empty.select.return_value = empty
        sb.table.return_value = empty

        with patch("routers.autenticacion.get_sb", return_value=sb):
            r = client.post(
                "/api/v1/auth/token",
                data={"username": "noexiste@x.co", "password": "cualquier"},
            )
        assert r.status_code == 401

    def test_password_incorrecto_retorna_401(self):
        hashed = hash_password("password-correcto")
        user = {**_FAKE_USER, "hashed_password": hashed}
        sb = MagicMock()
        chain = MagicMock()
        chain.execute.return_value = MagicMock(data=[user])
        chain.eq.return_value = chain
        chain.select.return_value = chain
        sb.table.return_value = chain

        with patch("routers.autenticacion.get_sb", return_value=sb):
            r = client.post(
                "/api/v1/auth/token",
                data={"username": "test@finpro.co", "password": "password-INCORRECTO"},
            )
        assert r.status_code == 401

    def test_error_no_revela_si_usuario_existe(self):
        """Ambos casos (user no existe / password mal) deben dar el mismo mensaje."""
        sb_empty = MagicMock()
        empty = MagicMock()
        empty.execute.return_value = MagicMock(data=[])
        empty.eq.return_value = empty
        empty.select.return_value = empty
        sb_empty.table.return_value = empty

        with patch("routers.autenticacion.get_sb", return_value=sb_empty):
            r1 = client.post("/api/v1/auth/token",
                             data={"username": "noexiste@x.co", "password": "x"})

        hashed = hash_password("correcta")
        user = {**_FAKE_USER, "hashed_password": hashed}
        sb_user = MagicMock()
        chain = MagicMock()
        chain.execute.return_value = MagicMock(data=[user])
        chain.eq.return_value = chain
        chain.select.return_value = chain
        sb_user.table.return_value = chain

        with patch("routers.autenticacion.get_sb", return_value=sb_user):
            r2 = client.post("/api/v1/auth/token",
                             data={"username": "test@finpro.co", "password": "incorrecta"})

        assert r1.json()["detail"] == r2.json()["detail"] == "Credenciales incorrectas"


# ═══════════════════════════════════════════════════════════════════════════════
# 6. ENDPOINTS PÚBLICOS
# ═══════════════════════════════════════════════════════════════════════════════
class TestEndpointsPublicos:

    def test_health_retorna_200(self):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["estado"] == "activo"

    def test_ui_retorna_html(self):
        r = client.get("/")
        assert r.status_code == 200
        assert "text/html" in r.headers.get("content-type", "")

    def test_endpoint_protegido_sin_auth_retorna_401(self):
        r = client.get("/api/v1/auth/me")
        assert r.status_code == 401

    def test_facturas_sin_auth_retorna_401(self):
        r = client.get("/api/v1/facturas/")
        assert r.status_code == 401
