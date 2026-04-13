"""
migrate.py — Ejecuta migraciones SQL contra Supabase usando la Management API.

Uso:
    python migrate.py

Requiere (una de las dos opciones):
  A) Variable de entorno SUPABASE_ACCESS_TOKEN  (token personal de Supabase)
     Obtener en: https://supabase.com/dashboard/account/tokens
  B) Argumento --token <token>

El project ref y la URL se leen automáticamente desde config.py / .env.
"""

import argparse
import os
import re
import sys
import json
from pathlib import Path

# ── leer configuración ────────────────────────────────────────────────────────
# Cargar .env manualmente para no depender de pydantic-settings en este script
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    for line in _env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

# Importar después de cargar .env
from config import settings  # noqa: E402

SUPABASE_URL = settings.SUPABASE_URL  # e.g. https://ucacmeyfybjdntieudsm.supabase.co


def _project_ref(url: str) -> str:
    """Extrae el project ref de la URL de Supabase."""
    m = re.match(r"https://([a-z0-9]+)\.supabase\.co", url)
    if not m:
        raise SystemExit(f"No se pudo extraer el project ref de: {url}")
    return m.group(1)


def run_sql(sql: str, token: str) -> dict:
    import subprocess
    ref = _project_ref(SUPABASE_URL)
    api_url = f"https://api.supabase.com/v1/projects/{ref}/database/query"
    payload = json.dumps({"query": sql})
    result = subprocess.run(
        ["curl", "-s", "-w", "\n__STATUS__%{http_code}", "-X", "POST", api_url,
         "-H", f"Authorization: Bearer {token}",
         "-H", "Content-Type: application/json",
         "-d", payload],
        capture_output=True, text=True, timeout=30,
    )
    output = result.stdout
    if "__STATUS__" in output:
        body, _, status = output.rpartition("\n__STATUS__")
        if not status.startswith("2"):
            raise SystemExit(f"Error HTTP {status} de la API de Supabase:\n{body}")
        return json.loads(body) if body.strip() else {}
    raise SystemExit(f"Error inesperado:\n{result.stdout}\n{result.stderr}")


MIGRATIONS_DIR = Path(__file__).parent / "migrations"

ALL_MIGRATIONS = [
    MIGRATIONS_DIR / "email_preferences.sql",
    MIGRATIONS_DIR / "gaps.sql",
]


def main():
    parser = argparse.ArgumentParser(description="Ejecutar migraciones en Supabase")
    parser.add_argument("--token", default=None, help="Personal access token de Supabase")
    parser.add_argument(
        "--file", default=None,
        help="Archivo SQL específico a ejecutar (por defecto: todos en migrations/)"
    )
    args = parser.parse_args()

    token = args.token or os.environ.get("SUPABASE_ACCESS_TOKEN", "")
    if not token:
        print(
            "ERROR: Se necesita el token personal de Supabase.\n"
            "  Opción A — variable de entorno:  SUPABASE_ACCESS_TOKEN=<token> python migrate.py\n"
            "  Opción B — argumento:             python migrate.py --token <token>\n"
            "  Obtener token en: https://supabase.com/dashboard/account/tokens"
        )
        sys.exit(1)

    files = [Path(args.file)] if args.file else ALL_MIGRATIONS

    project_ref = _project_ref(SUPABASE_URL)
    print(f"Proyecto Supabase: {project_ref}")
    print(f"URL: {SUPABASE_URL}\n")

    for sql_file in files:
        if not sql_file.exists():
            print(f"  [SKIP] {sql_file.name} — archivo no encontrado")
            continue
        sql = sql_file.read_text(encoding="utf-8").strip()
        print(f"  Ejecutando {sql_file.name} ...", end=" ", flush=True)
        try:
            result = run_sql(sql, token)
            print("OK")
            if isinstance(result, list) and result:
                print(f"    → {result}")
        except SystemExit as exc:
            print("FALLO")
            print(f"    {exc}")
            sys.exit(1)

    print("\nOK - Migraciones completadas exitosamente.")


if __name__ == "__main__":
    main()
