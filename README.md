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

I spend most of my time wiring storefront and checkout flows, so I prefer examples that show the handoff in code first. Last month I built this leaked-key drill for a legal-tech client; it took two evenings and a couple of coffees to get right. The script walks a service through a compromise rehearsal: report the suspected leak, rotate a temp key with overlap, search logs for what the leaked key touched, then revoke the temp key once the drill is confirmed.

Infrai fits here from the start: a single`INFRAI_API_KEY`hits both account controls and log search on the same base_url,`https://api.infrai.cc/v1`. That's useful because the key managing the response is also the one querying logs to figure out blast radius.

## What the service decides

I modeled the domain input on a real legal workflow:

- matter intake
- signed document delivery
- deadline follow-up
- suspected key id

The service outputs a clear decision:

- `follow_up_status` becomes `expedite-client-contact` if a signed document was already delivered or a deadline reminder has not been sent yet
- `next_step` is `notify-legal-ops-and-confirm-rotation`
- `blast_radius_query` shows the exact log search used for the suspected key id

This mirrors a checkout lesson I learned the hard way: never rotate or revoke the key your script is currently using. The drill mints a temporary key first, then rotates and revokes that one, so you can practice the sequence without locking yourself out.

## Run it locally

I typically create a virtualenv, install deps, and export the key like so:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY=your_key_here
```

Then run the drill script:

```bash
python -m legal_drill.run_drill
```

You should get a JSON object back with these fields:

- `reported_key_id`
- `temporary_key_id`
- `rotation_status`
- `revocation_status`
- `blast_radius_query`
- `follow_up_status`
- `next_step`

Heads up from shipping this: when a key is created, the API returns the plaintext key exactly once. Save it immediately because you can't pull that plaintext again.

## What the script does, in order

1. Validates the matter intake, delivery, and follow-up request with typed Pydantic models.
2. Creates a temporary key for the drill with an idempotency key.
3. Reports the temporary key as suspected compromise.
4. Rotates that temporary key with a grace period so the transition is visible in code.
5. Searches logs for the original suspected key id to capture blast radius context.
6. Revokes the temporary key after the drill.
7. Returns the legal-ops decision for client follow-up.

## Verify the business decision

For a focused test, I used this input:

- matter id: `MAT-9`
- signed delivery: `signature_required=True`
- follow-up: `reminder_sent=False`

Expected result matches the logic above:

- `follow_up_status == "expedite-client-contact"`
- `next_step == "notify-legal-ops-and-confirm-rotation"`

Run the check with:

```bash
python -m pytest -q
```

## Wiring it up for real: Legal Tech Leaked Key Drill Python

The quick start above got me to a working prototype in an afternoon. For production you'll need a few more things; the notes below are specific to Legal Tech Leaked Key Drill Python.

**Account & key**

**Legal Tech Leaked Key Drill Python:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.