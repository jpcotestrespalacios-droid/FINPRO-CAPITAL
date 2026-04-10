from fastapi import APIRouter  
router = APIRouter()  
@router.get("/ping-dian")  
async def ping_dian():  
    return {"disponible": True, "ambiente": "habilitacion"} 
