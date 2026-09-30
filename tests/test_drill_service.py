import pytest
from types import SimpleNamespace

from legal_drill import drill_service
from legal_drill.drill_service import decide_follow_up_status
from legal_drill.models import DeadlineFollowUp, LeakedKeyDrillRequest, MatterIntake, SignedDocumentDelivery


def test_expedite_follow_up_when_signed_delivery_exists_and_reminder_missing() -> None:
    request = LeakedKeyDrillRequest(
        suspect_key_id="key_live_123",
        matter=MatterIntake(
            matter_id="MAT-9",
            client_name="Harbor Shop",
            contact_email="owner@harbor.example",
            case_summary="Marketplace agreement review after leaked key alert.",
            jurisdiction="CA",
        ),
        signed_delivery=SignedDocumentDelivery(
            document_id="DOC-5",
            recipient_email="counsel@harbor.example",
            delivered_at="2026-09-23T10:00:00Z",
            signature_required=True,
        ),
        follow_up=DeadlineFollowUp(
            deadline_id="DL-1",
            due_at="2026-09-24T12:00:00Z",
            owner_email="paralegal@firm.example",
            reminder_sent=False,
        ),
    )

    result = decide_follow_up_status(request)

    assert result == "expedite-client-contact"


def test_temporary_key_is_revoked_when_drill_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    request = LeakedKeyDrillRequest(
        suspect_key_id="key_live_123",
        matter=MatterIntake(
            matter_id="MAT-9",
            client_name="Harbor Shop",
            contact_email="owner@harbor.example",
            case_summary="Marketplace agreement review after leaked key alert.",
            jurisdiction="CA",
        ),
        signed_delivery=SignedDocumentDelivery(
            document_id="DOC-5",
            recipient_email="counsel@harbor.example",
            delivered_at="2026-09-23T10:00:00Z",
            signature_required=True,
        ),
        follow_up=DeadlineFollowUp(
            deadline_id="DL-1",
            due_at="2026-09-24T12:00:00Z",
            owner_email="paralegal@firm.example",
            reminder_sent=False,
        ),
    )
    revoked = []

    keys = SimpleNamespace(
        create=lambda payload: {"id": "key_temp"},
        suspected_compromise=lambda key_id, payload: (_ for _ in ()).throw(RuntimeError("compromise failed")),
        revoke=revoked.append,
    )
    fake_infrai = SimpleNamespace(account=SimpleNamespace(keys=keys))
    monkeypatch.setattr(drill_service, "infrai", fake_infrai)

    with pytest.raises(RuntimeError, match="compromise failed"):
        drill_service.run_leaked_key_drill(request, idempotency_seed="test")

    assert revoked == ["key_temp"]
