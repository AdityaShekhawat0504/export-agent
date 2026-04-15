from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.schemas.schemas import ShipmentCreate, FeedbackRequest
from app.models.models import ExportShipment
from app.services.shipment import shipment_service
from app.services.feedback_service import apply_feedback

router = APIRouter()


# 🔌 DB Dependency
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# 🚀 CREATE SHIPMENT
@router.post("/shipments")
async def create_shipment(
    data: ShipmentCreate,
    db: AsyncSession = Depends(get_db)
):
    shipment = await shipment_service.create(data, db)

    await db.commit()
    await db.refresh(shipment)

    return shipment


# 📦 LIST SHIPMENTS
@router.get("/shipments")
async def list_shipments(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ExportShipment))
    return result.scalars().all()


# 🔥 FEEDBACK (HUMAN LEARNING LOOP)
@router.post("/feedback")
async def feedback(
    data: FeedbackRequest,
    db: AsyncSession = Depends(get_db)
):
    memory = await apply_feedback(
        description=data.description,
        correct_hs_code=data.hs_code,
        db=db
    )

    await db.commit()
    await db.refresh(memory)

    return {
        "message": "Feedback applied successfully",
        "hs_code": memory.hs_code,
        "source": memory.source
    }