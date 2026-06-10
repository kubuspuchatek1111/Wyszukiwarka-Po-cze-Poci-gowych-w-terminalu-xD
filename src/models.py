from dataclasses import dataclass

@dataclass(frozen=True)
class Stop:
    id: str
    name: str

@dataclass(frozen=True)
class Trip:
    id: str
    route_id: str
    service_id: str
    headsign: str
    train_number: str

@dataclass(frozen=True)
class StopTime:
    trip_id: str
    stop_id: str
    stop_sequence: int
    arrival_minutes: int
    departure_minutes: int
    platform: str  # Dodany peron
    track: str     # Dodany tor

@dataclass
class RouteLeg:
    trip: Trip
    from_stop_id: str
    to_stop_id: str
    departure_time_str: str
    arrival_time_str: str
    departure_minutes_absolute: int
    arrival_minutes_absolute: int
    duration_minutes: int
    from_platform: str  # Informacja o peronie startowym
    from_track: str     # Informacja o torze startowym
    to_platform: str    # Informacja o peronie docelowym
    to_track: str       # Informacja o torze docelowym

@dataclass
class CompleteJourney:
    legs: list[RouteLeg]
    
    @property
    def total_duration(self) -> int:
        if not self.legs:
            return 0
        return self.legs[-1].arrival_minutes_absolute - self.legs[0].departure_minutes_absolute

    @property
    def departure_time_str(self) -> str:
        return self.legs[0].departure_time_str

    @property
    def arrival_time_str(self) -> str:
        return self.legs[-1].arrival_time_str