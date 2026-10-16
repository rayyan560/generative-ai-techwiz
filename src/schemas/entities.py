from typing import List, Optional

from pydantic import BaseModel, Field


class EntityExtractionResult(BaseModel):
    order_id: Optional[str] = None
    transaction_id: Optional[str] = None
    product_name: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = "USD"
    incident_date: Optional[str] = None
    serial_number: Optional[str] = None
    location: Optional[str] = None
    tracking_number: Optional[str] = None


class ComplaintSubmission(BaseModel):
    complaint_id: Optional[str] = None
    customer_id: str = "CUST-1001"
    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = None
    customer_type: str = "Standard"
    complaint_title: str
    complaint_description: str
    product_or_service: Optional[str] = None
    order_reference: Optional[str] = None
    transaction_reference: Optional[str] = None
    preferred_channel: str = "Web Form"
    attachment_names: List[str] = Field(default_factory=list)
    previous_complaint_id: Optional[str] = None
    created_at: Optional[str] = None
