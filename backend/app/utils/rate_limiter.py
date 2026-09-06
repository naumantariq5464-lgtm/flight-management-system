import time
from collections import defaultdict
from fastapi import Request, HTTPException, status
from typing import Dict, List, Tuple

class RateLimiter:
    """
    In-Memory Sliding Window Rate Limiter for FastAPI endpoints.
    Protects sensitive routes like /auth/login and /auth/register from brute-force attacks.
    """
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # Mapping: client_identifier -> list of timestamps
        self._history: Dict[str, List[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        # Check X-Forwarded-For if behind reverse proxy
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def __call__(self, request: Request):
        client_ip = self._get_client_ip(request)
        route_key = f"{request.url.path}:{client_ip}"
        now = time.time()
        window_start = now - self.window_seconds

        # Clean timestamps older than the sliding window
        timestamps = [t for t in self._history[route_key] if t > window_start]
        self._history[route_key] = timestamps

        if len(timestamps) >= self.max_requests:
            oldest = timestamps[0]
            retry_after = int(self.window_seconds - (now - oldest)) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: Maximum {self.max_requests} requests per {self.window_seconds}s. Please retry in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)}
            )

        # Record this request
        self._history[route_key].append(now)

# Predefined rate limiters for authentication endpoints:
# 1. Login: Max 5 attempts per 60 seconds per IP
login_rate_limiter = RateLimiter(max_requests=5, window_seconds=60)

# 2. Register: Max 3 accounts per 60 seconds per IP
register_rate_limiter = RateLimiter(max_requests=3, window_seconds=60)
