import time
from fastapi import APIRouter
from config import settings

router = APIRouter()


@router.get("/ping-dian", summary="Verificar conectividad con webservices DIAN")
async def ping_dian():
    """Verifica conectividad real con el WSDL de la DIAN y mide latencia."""
    import urllib.request
    import urllib.error

    wsdl_url = settings.DIAN_WS_RADIAN_WSDL
    ambiente = "produccion" if settings.DIAN_AMBIENTE == "1" else "habilitacion"
    start = time.time()
    try:
        req = urllib.request.Request(wsdl_url, method="HEAD")
        with urllib.request.urlopen(req, timeout=5):
            pass
        latencia_ms = int((time.time() - start) * 1000)
        return {"disponible": True, "ambiente": ambiente, "latencia_ms": latencia_ms, "url": wsdl_url}
    except Exception as exc:
        latencia_ms = int((time.time() - start) * 1000)
        return {"disponible": False, "ambiente": ambiente, "latencia_ms": latencia_ms, "error": str(exc)}

