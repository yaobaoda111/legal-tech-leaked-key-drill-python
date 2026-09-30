import json

from .drill_service import run_leaked_key_drill
from .models import DeadlineFollowUp, LeakedKeyDrillRequest, MatterIntake, SignedDocumentDelivery


def main() -> None:
    request = LeakedKeyDrillRequest(
        suspect_key_id="key_live_123",
        matter=MatterIntake(
            matter_id="MAT-2048",
            client_name="Rivera Imports",
            contact_email="ops@rivera.example",
            case_summary="Vendor agreement intake tied to a leaked integration key.",
            jurisdiction="NY",
        ),
        signed_delivery=SignedDocumentDelivery(
            document_id="DOC-77",
            recipient_email="counsel@rivera.example",
            delivered_at="2026-09-23T15:30:00Z",
            signature_required=True,
        ),
        follow_up=DeadlineFollowUp(
            deadline_id="DL-55",
            due_at="2026-09-25T17:00:00Z",
            owner_email="paralegal@firm.example",
            reminder_sent=False,
        ),
    )
    result = run_leaked_key_drill(request)
    print(json.dumps(result.model_dump(), indent=2))


if __name__ == "__main__":
    main()
