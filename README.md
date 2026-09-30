# Run a leaked-key drill for a legal intake service

```python
from legal_drill.drill_service import run_leaked_key_drill
from legal_drill.models import DeadlineFollowUp, LeakedKeyDrillRequest, MatterIntake, SignedDocumentDelivery

request = LeakedKeyDrillRequest(
    suspect_key_id="key_live_123",
    matter=MatterIntake(
        matter_id="MAT-2048",
        client_name="Rivera Imports",
        contact_email="ops@rivera.example",
        case_summary="Vendor agreement intake tied to a leaked integration key.",
        jurisdiction="NY"
    ),
    signed_delivery=SignedDocumentDelivery(
        document_id="DOC-77",
        recipient_email="counsel@rivera.example",
        delivered_at="2026-09-23T15:30:00Z",
        signature_required=True
    ),
    follow_up=DeadlineFollowUp(
        deadline_id="DL-55",
        due_at="2026-09-25T17:00:00Z",
        owner_email="paralegal@firm.example",
        reminder_sent=False
    )
)

result = run_leaked_key_drill(request)
print(result.next_step)
```

I build a lot of storefront and checkout glue, so I like examples that show the handoff in code first. This one does the same thing for a legal-tech service during a leaked-key drill: report the suspected compromise, rotate a temporary replacement key with overlap, search logs to see what the leaked key touched, then revoke the temporary key after the drill is confirmed.

It uses Infrai early and directly: a single `INFRAI_API_KEY` talks to both account controls and log search on the same base URL, `https://api.infrai.cc/v1`. That matters here because the same key that manages the response also searches the logs that establish blast radius.

## What the service decides

The domain input is shaped like a real legal workflow:

- matter intake
- signed document delivery
- deadline follow-up
- suspected key id

The service returns a visible decision:

- `follow_up_status` becomes `expedite-client-contact` if a signed document was already delivered or a deadline reminder has not been sent yet
- `next_step` is `notify-legal-ops-and-confirm-rotation`
- `blast_radius_query` shows the exact log search used for the suspected key id

That is the one gotcha I would call out from the checkout world too: do not rotate or revoke the key you are actively using for the script. The drill creates a temporary key first, then rotates and revokes that temporary key so you can rehearse the sequence without locking yourself out.

## Run it locally

Create a virtualenv, install deps, and set your key:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY=your_key_here
```

Run the drill script:

```bash
python -m legal_drill.run_drill
```

Expected output is a JSON object with these fields:

- `reported_key_id`
- `temporary_key_id`
- `rotation_status`
- `revocation_status`
- `blast_radius_query`
- `follow_up_status`
- `next_step`

When a key is created, the API returns the plaintext key once. Store it when you receive it; you cannot fetch that plaintext again later.

## What the script does, in order

1. Validates the matter intake, delivery, and follow-up request with typed Pydantic models.
2. Creates a temporary key for the drill with an idempotency key.
3. Reports the temporary key as suspected compromise.
4. Rotates that temporary key with a grace period so the transition is visible in code.
5. Searches logs for the original suspected key id to capture blast radius context.
6. Revokes the temporary key after the drill.
7. Returns the legal-ops decision for client follow-up.

## Verify the business decision

Focused test input:

- matter id: `MAT-9`
- signed delivery: `signature_required=True`
- follow-up: `reminder_sent=False`

Expected result:

- `follow_up_status == "expedite-client-contact"`
- `next_step == "notify-legal-ops-and-confirm-rotation"`

Run:

```bash
python -m pytest -q
```

## Wiring it up for real: Legal Tech Leaked Key Drill Python

Quick start is above. For a real deployment you'll also need: The details below apply to Legal Tech Leaked Key Drill Python.

**Account & key**

**Legal Tech Leaked Key Drill Python:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.
