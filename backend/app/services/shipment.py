from app.models.models import ExportShipment
from app.services.decision_engine import classify_with_intelligence
from app.services.risk_engine import evaluate_risk


class ShipmentService:

    async def create(self, data, db):

        # 🔥 STEP 1: Get intelligence (AI + Memory)
        decision = await classify_with_intelligence(db, data.description)

        hs_code = decision["hs_code"]
        confidence = decision["confidence"]
        source = decision["source"]

        # 🔥 STEP 2: Risk evaluation (separate engine)
        risk = evaluate_risk(data.destination_country, confidence)

        status = risk["status"]
        blocked = risk["blocked"]
        reason = f"{risk['reason']} ({source})"

        # 🔥 STEP 3: Create shipment
        shipment = ExportShipment(
            description=data.description,
            destination_country=data.destination_country,
            counterparty_name=data.counterparty_name,
            status=status,
            blocked=blocked,
            decision_reason=reason,

            # 🔥 Intelligence fields (VERY IMPORTANT)
            hs_code=hs_code,
            confidence=confidence,
            source=source
        )

        db.add(shipment)
        await db.commit()
        await db.refresh(shipment)

        return shipment


shipment_service = ShipmentService()