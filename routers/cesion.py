"""
Router de Cesión de Facturas - RADIAN
Endpoints para ceder facturas electrónicas como título valor
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from database import get_db, Factura, Cesion, EstadoFactura, EstadoCesion, Usuario
from services.dian_radian import dian_service
from routers.autenticacion import get_current_user

router = APIRouter()


# ── Esquemas Pydantic ──────────────────────────────────────────────────────────

class CesionRequest(BaseModel):
    cufe_factura: str
    cesionario_nit: str
    cesionario_nombre: str
    valor_cesion: float
    descripcion: Optional[str] = "Endoso en propiedad - cesión de factura electrónica"

class CesionResponse(BaseModel):
    id: int
    cude: str
    cufe_factura: str
    cedente_nit: str
    cesionario_nit: str
    valor_cesion: float
    estado: str
    fecha_cesion: datetime
    mensaje: str


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/crear", response_model=CesionResponse, summary="Ceder una factura electrónica")
async def crear_cesion(
    data: CesionRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    ## Cede una factura electrónica como título valor en RADIAN
    
    **Proceso:**
    1. Valida que la factura exista y sea endosable
    2. Construye el XML del evento 037 (Endoso en Propiedad)
    3. Firma digitalmente el XML
    4. Envía el evento al webservice RADIAN de la DIAN
    5. Registra el resultado
    
    **Prerrequisitos:**
    - La factura debe estar validada por la DIAN
    - El adquiriente debe haber aceptado la factura (evento 032)
    - No debe existir una manifestación de pago previo (evento 045)
    """

    # 1. Buscar factura
    factura = db.query(Factura).filter(Factura.cufe == data.cufe_factura).first()
    if not factura:
        raise HTTPException(status_code=404, detail=f"Factura con CUFE {data.cufe_factura} no encontrada")

    # Verificar que el usuario autenticado sea el emisor de la factura
    if factura.emisor_nit != current_user.nit:
        raise HTTPException(status_code=403, detail="Solo el emisor de la factura puede realizar la cesión")

    # 2. Validar que sea endosable
    if not factura.es_titulo_valor:
        raise HTTPException(
            status_code=400,
            detail="La factura no está habilitada como título valor. El adquiriente debe aceptarla primero."
        )

    if factura.estado == EstadoFactura.CEDIDA:
        raise HTTPException(status_code=400, detail="Esta factura ya fue cedida anteriormente")

    if factura.estado == EstadoFactura.PAGADA:
        raise HTTPException(status_code=400, detail="Esta factura ya fue pagada, no se puede ceder")

    # 3. Generar número de cesión
    total_cesiones = db.query(Cesion).count()
    numero_cesion = f"CES{datetime.now().year}{str(total_cesiones + 1).zfill(8)}"

    fecha_cesion = datetime.now()

    # 4. Construir XML del evento de cesión
    xml_evento, cude = dian_service.construir_xml_cesion(
        cufe_factura=data.cufe_factura,
        numero_cesion=numero_cesion,
        cedente_nit=factura.emisor_nit,
        cedente_nombre=factura.emisor_nombre,
        cesionario_nit=data.cesionario_nit,
        cesionario_nombre=data.cesionario_nombre,
        deudor_nit=factura.adquiriente_nit,
        deudor_nombre=factura.adquiriente_nombre,
        valor_cesion=data.valor_cesion,
        fecha_cesion=fecha_cesion
    )

    # 5. Firmar XML
    xml_firmado = dian_service.firmar_xml(xml_evento)

    # 6. Enviar a DIAN RADIAN
    respuesta_dian = dian_service.enviar_evento_radian(xml_firmado)

    # 7. Registrar en BD
    nueva_cesion = Cesion(
        factura_id=factura.id,
        cufe_factura=data.cufe_factura,
        cedente_nit=factura.emisor_nit,
        cedente_nombre=factura.emisor_nombre,
        cesionario_nit=data.cesionario_nit,
        cesionario_nombre=data.cesionario_nombre,
        deudor_nit=factura.adquiriente_nit,
        deudor_nombre=factura.adquiriente_nombre,
        valor_cesion=data.valor_cesion,
        cude=cude,
        numero_cesion=numero_cesion,
        fecha_cesion=fecha_cesion,
        xml_evento=xml_firmado,
        xml_respuesta_dian=str(respuesta_dian),
        estado=EstadoCesion.ACEPTADA if respuesta_dian["exitoso"] else EstadoCesion.RECHAZADA,
        descripcion_estado=respuesta_dian.get("descripcion", "")
    )
    db.add(nueva_cesion)

    # 8. Actualizar estado de la factura
    if respuesta_dian["exitoso"]:
        factura.estado = EstadoFactura.CEDIDA

    db.commit()
    db.refresh(nueva_cesion)

    return CesionResponse(
        id=nueva_cesion.id,
        cude=cude,
        cufe_factura=data.cufe_factura,
        cedente_nit=factura.emisor_nit,
        cesionario_nit=data.cesionario_nit,
        valor_cesion=data.valor_cesion,
        estado=nueva_cesion.estado,
        fecha_cesion=fecha_cesion,
        mensaje="✅ Cesión registrada en RADIAN exitosamente" if respuesta_dian["exitoso"] else f"❌ Error DIAN: {respuesta_dian.get('descripcion')}"
    )


@router.get("/{cude}/estado", summary="Consultar estado de cesión en DIAN")
async def consultar_estado_cesion(
    cude: str,
    db: Session = Depends(get_db),
    _current_user: Usuario = Depends(get_current_user),
):
    """Consulta el estado actual de un evento de cesión en RADIAN por su CUDE"""
    
    cesion = db.query(Cesion).filter(Cesion.cude == cude).first()
    if not cesion:
        raise HTTPException(status_code=404, detail="Cesión no encontrada")

    # Consultar en tiempo real a la DIAN
    estado_dian = dian_service.consultar_estado_evento(cude)

    return {
        "cude": cude,
        "estado_local": cesion.estado,
        "estado_dian": estado_dian,
        "fecha_cesion": cesion.fecha_cesion,
        "cedente": cesion.cedente_nombre,
        "cesionario": cesion.cesionario_nombre,
        "valor": cesion.valor_cesion
    }


@router.get("/factura/{cufe}", summary="Ver cesiones de una factura")
async def cesiones_por_factura(
    cufe: str,
    db: Session = Depends(get_db),
    _current_user: Usuario = Depends(get_current_user),
):
    """Lista el historial completo de cesiones de una factura"""
    cesiones = db.query(Cesion).filter(Cesion.cufe_factura == cufe).all()
    if not cesiones:
        return {"cufe": cufe, "cesiones": [], "total": 0}
    
    return {
        "cufe": cufe,
        "total": len(cesiones),
        "cesiones": [
            {
                "id": c.id,
                "cude": c.cude,
                "cedente": c.cedente_nombre,
                "cesionario": c.cesionario_nombre,
                "valor": c.valor_cesion,
                "estado": c.estado,
                "fecha": c.fecha_cesion
            }
            for c in cesiones
        ]
    }


@router.get("/xml/{cude}", summary="Descargar XML del evento de cesión")
async def descargar_xml_cesion(
    cude: str,
    db: Session = Depends(get_db),
    _current_user: Usuario = Depends(get_current_user),
):
    """Retorna el XML firmado del evento de cesión enviado a la DIAN"""
    cesion = db.query(Cesion).filter(Cesion.cude == cude).first()
    if not cesion:
        raise HTTPException(status_code=404, detail="Cesión no encontrada")
    
    from fastapi.responses import Response
    return Response(
        content=cesion.xml_evento,
        media_type="application/xml",
        headers={"Content-Disposition": f"attachment; filename=cesion_{cude[:16]}.xml"}
    )
