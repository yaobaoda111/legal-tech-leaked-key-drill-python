import uuid
from typing import Optional

from .infrai_client import build_log_query_for_key, encode_query, infrai
from .models import LeakedKeyDrillRequest, LeakedKeyDrillResult


def decide_follow_up_status(request: LeakedKeyDrillRequest) -> str:
    if request.signed_delivery.signature_required or not request.follow_up.reminder_sent:
        return "expedite-client-contact"
    return "standard-monitoring"


def run_leaked_key_drill(request: LeakedKeyDrillRequest, idempotency_seed: Optional[str] = None) -> LeakedKeyDrillResult:
    seed = idempotency_seed or str(uuid.uuid4())

    created_key = infrai.account.keys.create(
        {
            "name": f"drill-{request.matter.matter_id}",
            "scopes": ["logs.search"],
            "idempotency_key": f"create-{seed}",
        }
    )
    temporary_key_id = created_key["id"]

    try:
        infrai.account.keys.suspected_compromise(
            temporary_key_id,
            {
                "confirmed_leak": True,
                "auto_rotate": False,
            },
        )

        infrai.account.keys.rotate(
            temporary_key_id,
            {
                "grace_hours": 2,
                "idempotency_key": f"rotate-{seed}",
            },
        )

        log_query = build_log_query_for_key(request.suspect_key_id)
        infrai.logs.search(log_query)
    finally:
        infrai.account.keys.revoke(temporary_key_id)

    return LeakedKeyDrillResult(
        reported_key_id=request.suspect_key_id,
        temporary_key_id=temporary_key_id,
        rotation_status="rotated-with-grace-period",
        revocation_status="temporary-key-revoked",
        blast_radius_query=f"/v1/logs/search?{encode_query(log_query)}",
        follow_up_status=decide_follow_up_status(request),
        next_step="notify-legal-ops-and-confirm-rotation",
    )
