from pydantic import BaseModel
from decimal import Decimal
from typing import List, Dict, Any

class DashboardStats(BaseModel):
    total_flights: int
    active_flights: int
    cancelled_flights: int
    total_bookings: int
    confirmed_bookings: int
    pending_bookings: int
    available_seats: int
    load_factor_percentage: float
    total_revenue: Decimal
    currency: str = "USD"
    pending_refunds: int
    waitlisted_passengers: int
    fraud_alerts: int
    failed_automations: int

class RevenueTrendPoint(BaseModel):
    date: str
    revenue: Decimal
    bookings_count: int

class FlightOccupancyStat(BaseModel):
    flight_number: str
    route: str
    total_capacity: int
    booked_seats: int
    occupancy_rate: float
    status: str

class ReportResponse(BaseModel):
    summary: DashboardStats
    revenue_trend: List[RevenueTrendPoint]
    top_routes: List[Dict[str, Any]]
    occupancy_breakdown: List[FlightOccupancyStat]
