import uuid
from sqlalchemy import Column, String, Boolean, Float, Integer, Text
from app.core.database import Base


class ExportShipment(Base):
    __tablename__ = "export_shipments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    description = Column(Text)
    destination_country = Column(String)
    counterparty_name = Column(String)

    # 🔥 INTELLIGENCE STORAGE (CRITICAL)
    hs_code = Column(String)
    confidence = Column(Float)
    source = Column(String)  # ai / memory / human_feedback

    status = Column(String)
    blocked = Column(Boolean, default=False)
    decision_reason = Column(Text)


class ProductMemory(Base):
    __tablename__ = "product_memory"

    # 🔥 fingerprint = PRIMARY KEY (VERY IMPORTANT)
    id = Column(String, primary_key=True)

    fingerprint = Column(String, unique=True)
    normalized_name = Column(Text)

    hs_code = Column(String)
    confidence = Column(Float)

    source = Column(String)  # ai / human_feedback

    total_observations = Column(Integer, default=1)
    memory_hits = Column(Integer, default=0)