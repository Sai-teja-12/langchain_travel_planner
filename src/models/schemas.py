from typing import List, Optional
from pydantic import BaseModel, Field


class TravelRequest(BaseModel):
    origin: str = Field(..., description="Departure city or airport code which is 3-letter IATA code of the departure airport. Must be capitalized (e.g., 'BLR')")
    destination: str = Field(..., description="Arrival city or airport code which is 3-letter IATA code of the arrival airport. Must be capitalized (e.g., 'FCO')")
    departure_date: str = Field(..., description="Departure date (YYYY-MM-DD)")
    return_date: str = Field(..., description="Return date (YYYY-MM-DD)")
    travelers: int = Field(1, description="Number of travelers")
    budget: Optional[float] = Field(None, description="Maximum budget for the trip")
    preferences: Optional[str] = Field(None, description="Any specific preferences or requirements")


class Activity(BaseModel):
    name: str = Field(..., description="Name of the activity")
    description: str = Field(..., description="Description of the activity")
    cost: float


class DayItinerary(BaseModel):
    date: str = Field(..., description="Date of the day (YYYY-MM-DD)")
    activities: List[Activity]


class FlightOption(BaseModel):
    airline: str = Field(..., description="Name of the airline")
    flight_number: str = Field(..., description="Flight number")
    departure_airport: str = Field(..., description="3-letter IATA code of the departure airport")
    arrival_airport: str = Field(..., description="3-letter IATA code of the arrival airport")
    departure_time: str = Field(..., description="Departure time (HH:MM)")
    arrival_time: str = Field(..., description="Arrival time (HH:MM)")
    price: float = Field(
        ...,
        description=(
            "For round trips: TOTAL round-trip fare for all travelers on OUTBOUND "
            "options only. Return options must use price=0 (fare already counted)."
        ),
    )
    direction: str = Field(
        "outbound",
        description="'outbound' (departure date) or 'return' (return date)",
    )


class HotelOption(BaseModel):
    name: str = Field(..., description="Name of the hotel")
    address: str = Field(..., description="Address of the hotel")
    price_per_night: float = Field(..., description="Price per night of the hotel")
    rating: float


class BudgetBreakdown(BaseModel):
    flights_cost: float
    hotels_cost: float
    activities_cost: float
    total_cost: float


class TripPlan(BaseModel):
    summary: str
    flights: List[FlightOption]
    hotels: List[HotelOption]
    itinerary: List[DayItinerary]
    budget: BudgetBreakdown
    travel_tips: List[str]