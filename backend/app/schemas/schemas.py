from pydantic import BaseModel


class ShipmentCreate(BaseModel):
    description: str
    destination_country: str
    counterparty_name: str


class FeedbackRequest(BaseModel):
    description: str
    hs_code: str