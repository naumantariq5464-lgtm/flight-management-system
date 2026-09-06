import httpx
import asyncio
import json

WEBHOOK_URL = "https://smithackathon.app.n8n.cloud/webhook/flight-events"

EVENTS_TO_TEST = [
    {
        "name": "1. Waitlist Auto-Promotion Event",
        "payload": {
            "event_type": "WAITLIST_PROMOTION",
            "flight_number": "PA-786",
            "customer_email": "customer@flightsystem.com",
            "message": "Testing automatic seat promotion via n8n"
        }
    },
    {
        "name": "2. Check-in Reminder Event",
        "payload": {
            "event_type": "CHECKIN_REMINDER",
            "flight_number": "PA-786",
            "pnr": "PNR-TEST-99",
            "customer_email": "customer@flightsystem.com",
            "message": "Testing 24h check-in email alert"
        }
    },
    {
        "name": "3. Refund SLA Escalation Alert",
        "payload": {
            "event_type": "REFUND_ESCALATION",
            "pnr": "PNR-REFUND-77",
            "customer_email": "admin@flightsystem.com",
            "message": "Testing SLA escalation for pending refund"
        }
    },
    {
        "name": "4. Daily Ops KPI Report Event",
        "payload": {
            "event_type": "DAILY_OPS_REPORT",
            "customer_email": "admin@flightsystem.com",
            "message": "Testing midnight executive operations report"
        }
    },
    {
        "name": "5. Live Flight Cancellation Event",
        "payload": {
            "event_type": "FLIGHT_CANCELLED",
            "flight_number": "PA-786",
            "customer_email": "customer@flightsystem.com",
            "message": "Flight PA-786 has been cancelled due to weather. Full refund or rebooking available."
        }
    }
]

async def run_tests():
    print("=" * 65)
    print("[TEST SUITE] TESTING N8N UNIFIED MASTER AUTOMATION WORKFLOW")
    print(f"Target Webhook: {WEBHOOK_URL}")
    print("=" * 65)

    async with httpx.AsyncClient(timeout=15.0) as client:
        for item in EVENTS_TO_TEST:
            print(f"\n>> Sending: {item['name']}...")
            try:
                res = await client.post(WEBHOOK_URL, json=item["payload"])
                if res.status_code in [200, 201]:
                    print(f"   [SUCCESS - {res.status_code}] Event received by n8n Switch Router!")
                else:
                    print(f"   [RESPONSE - {res.status_code}] {res.text}")
            except Exception as e:
                print(f"   [ERROR] {e}")
            await asyncio.sleep(1)

    print("\n" + "=" * 65)
    print("[COMPLETE] All test events dispatched! Check your 'Executions' tab in n8n Cloud.")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(run_tests())
