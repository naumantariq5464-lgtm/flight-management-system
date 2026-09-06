import httpx
import logging
from typing import Dict, Any, Optional
from app.config.settings import settings

logger = logging.getLogger("FlightSystem.n8n")

async def trigger_n8n_webhook(event_type: str, data: Dict[str, Any]) -> bool:
    """
    Sends an event payload to the exact n8n Cloud Webhook endpoint.
    """
    target_url = settings.N8N_WEBHOOK_URL or f"{settings.N8N_BASE_URL.rstrip('/')}/webhook/flight-events"

    payload = {
        "event_type": event_type,
        **data
    }

    headers = {
        "Content-Type": "application/json",
        "X-N8N-Secret": settings.N8N_WEBHOOK_SECRET
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(target_url, json=payload, headers=headers)
            if response.status_code in [200, 201]:
                logger.info(f"✅ Successfully triggered n8n webhook for event: {event_type}")
                return True
            else:
                logger.warning(f"⚠️ n8n webhook responded with status: {response.status_code}")
                return False
    except Exception as e:
        logger.warning(f"⚠️ Could not trigger n8n webhook (non-blocking): {e}")
        return False
