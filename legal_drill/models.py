from pydantic import BaseModel, EmailStr, Field


class MatterIntake(BaseModel):
    matter_id: str = Field(min_length=1)
    client_name: str = Field(min_length=1)
    contact_email: EmailStr
    case_summary: str = Field(min_length=1)
    jurisdiction: str = Field(min_length=1)


class SignedDocumentDelivery(BaseModel):
    document_id: str = Field(min_length=1)
    recipient_email: EmailStr
    delivered_at: str = Field(min_length=1)
    signature_required: bool


class DeadlineFollowUp(BaseModel):
    deadline_id: str = Field(min_length=1)
    due_at: str = Field(min_length=1)
    owner_email: EmailStr
    reminder_sent: bool


class LeakedKeyDrillRequest(BaseModel):
    suspect_key_id: str = Field(min_length=1)
    matter: MatterIntake
    signed_delivery: SignedDocumentDelivery
    follow_up: DeadlineFollowUp


class LeakedKeyDrillResult(BaseModel):
    reported_key_id: str
    temporary_key_id: str
    rotation_status: str
    revocation_status: str
    blast_radius_query: str
    follow_up_status: str
    next_step: str
