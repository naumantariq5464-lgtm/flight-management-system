import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from pydantic import ValidationError
from app.schemas.flight import FlightCreate
from app.utils.enums import OverbookingPolicy

def test_valid_flight_creation_schema():
    now = datetime.now(timezone.utc)
    dep = now + timedelta(days=5)
    arr = dep + timedelta(hours=3, minutes=30)
    
    # 20 First + 30 Business + 50 Economy = 100 Capacity
    flight_data = FlightCreate(
        flight_number="PK-301",
        origin="LHE",
        destination="DXB",
        departure_time=dep,
        arrival_time=arr,
        aircraft_capacity=100,
        first_class_seats=20,
        business_class_seats=30,
        economy_seats=50,
        base_price_economy=Decimal("350.00"),
        base_price_business=Decimal("800.00"),
        base_price_first=Decimal("1500.00"),
        currency="USD"
    )
    assert flight_data.aircraft_capacity == 100
    assert flight_data.flight_number == "PK-301"

def test_reject_seat_sum_mismatch():
    now = datetime.now(timezone.utc)
    dep = now + timedelta(days=5)
    arr = dep + timedelta(hours=3)
    
    # 20 + 30 + 40 = 90 != 100 Capacity -> MUST RAISE ERROR
    with pytest.raises(ValidationError) as exc:
        FlightCreate(
            flight_number="PK-301",
            origin="LHE",
            destination="DXB",
            departure_time=dep,
            arrival_time=arr,
            aircraft_capacity=100,
            first_class_seats=20,
            business_class_seats=30,
            economy_seats=40,
            base_price_economy=Decimal("350.00"),
            base_price_business=Decimal("800.00"),
            base_price_first=Decimal("1500.00")
        )
    assert "Seat breakdown sum" in str(exc.value)

def test_reject_arrival_before_departure():
    now = datetime.now(timezone.utc)
    dep = now + timedelta(days=5)
    arr = dep - timedelta(hours=1) # Arrival before departure!
    
    with pytest.raises(ValidationError) as exc:
        FlightCreate(
            flight_number="PK-301",
            origin="LHE",
            destination="DXB",
            departure_time=dep,
            arrival_time=arr,
            aircraft_capacity=50,
            first_class_seats=0,
            business_class_seats=10,
            economy_seats=40,
            base_price_economy=Decimal("350.00"),
            base_price_business=Decimal("800.00"),
            base_price_first=Decimal("0.00")
        )
    assert "arrival_time must be strictly after departure_time" in str(exc.value)
