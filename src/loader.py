import csv
import os
from typing import Dict, List, Set
from src.models import Stop, Trip, StopTime

class GTFSLoader:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.stops: Dict[str, Stop] = {}
        self.stop_name_to_id: Dict[str, str] = {}
        self.trips: Dict[str, Trip] = {}
        self.stop_departures: Dict[str, List[StopTime]] = {}
        self.trip_sequences: Dict[str, List[StopTime]] = {}
        self.calendar_services: Dict[str, Set[str]] = {}

    @staticmethod
    def parse_time_to_minutes(time_str: str) -> int:
        parts = list(map(int, time_str.strip().split(':')))
        return parts[0] * 60 + parts[1]

    @staticmethod
    def format_minutes_to_clock_time(minutes: int) -> str:
        """
        NORMALIZACJA CZASU: Konwertuje skumulowane minuty na standardowy
        format zegarowy 24-godzinny (00:00 - 23:59).
        """
        normalized_minutes = minutes % 1440
        hours = normalized_minutes // 60
        mins = normalized_minutes % 60
        return f"{hours:02d}:{mins:02d}"

    def load(self) -> None:
        self._load_stops()
        self._load_calendar()
        self._load_trips()
        self._load_stop_times()

    def _load_stops(self) -> None:
        with open(os.path.join(self.data_dir, "stops.txt"), mode="r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                s_id = row["stop_id"].strip()
                name = row["stop_name"].strip()
                self.stops[s_id] = Stop(id=s_id, name=name)
                self.stop_name_to_id[name.lower()] = s_id

    def _load_calendar(self) -> None:
        with open(os.path.join(self.data_dir, "calendar_dates.txt"), mode="r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                service_id = row["service_id"].strip()
                date_str = row["date"].strip()
                if row["exception_type"].strip() == "1":
                    if service_id not in self.calendar_services:
                        self.calendar_services[service_id] = set()
                    self.calendar_services[service_id].add(date_str)

    def _load_trips(self) -> None:
        with open(os.path.join(self.data_dir, "trips.txt"), mode="r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                t_id = row["trip_id"].strip()
                train_num = row.get("plk_train_number", row.get("trip_short_name", "Pociąg")).strip()
                
                self.trips[t_id] = Trip(
                    id=t_id,
                    route_id=row["route_id"].strip(),
                    service_id=row["service_id"].strip(),
                    headsign=row.get("trip_headsign", "Kierunek nieznany").strip(),
                    train_number=train_num if train_num else "Pociąg"
                )

    def _load_stop_times(self) -> None:
        with open(os.path.join(self.data_dir, "stop_times.txt"), mode="r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                try:
                    t_id = row["trip_id"].strip()
                    s_id = row["stop_id"].strip()
                    
                    if t_id not in self.trips or s_id not in self.stops:
                        continue
                    
                    raw_platform = row.get("platform", "-").strip()
                    raw_track = row.get("track", "-").strip()
                    
                    platform = raw_platform if raw_platform else "-"
                    track = raw_track if raw_track else "-"

                    # --- ZAAWANSOWANA DWUKIERUNKOWA SANITYZACJA PERON/TOR PKP PLK ---
                    
                    # Przypadek 1: Sklejone w kolumnie 'platform' (np. platform="12", track="-") -> Peron 1, Tor 2
                    if len(platform) == 2 and platform.isdigit() and (track == "-" or track == ""):
                        track = platform[1]
                        platform = platform[0]
                    
                    # Przypadek 2: Sklejone w kolumnie 'track' (np. platform="-", track="12") -> Peron 1, Tor 2
                    elif len(track) == 2 and track.isdigit() and (platform == "-" or platform == ""):
                        platform = track[0]
                        track = track[1]
                    
                    # Przypadek 3: Obie kolumny uzupełnione, ale tor powtarza peron (np. platform="1", track="12") -> TWOJA SYTUACJA
                    elif len(track) == 2 and track.isdigit() and platform != "-" and track[0] == platform:
                        track = track[1]  # Odrzucamy pierwszą cyfrę, zostawiamy właściwy tor
                        
                    # Przypadek 4: Obie kolumny uzupełnione, ale peron zawiera tor (np. platform="12", track="2")
                    elif len(platform) == 2 and platform.isdigit() and track != "-" and platform[1] == track:
                        platform = platform[0]
                    # -------------------------------------------------------------------------------
                        
                    st = StopTime(
                        trip_id=t_id,
                        stop_id=s_id,
                        stop_sequence=int(row["stop_sequence"]),
                        arrival_minutes=self.parse_time_to_minutes(row["arrival_time"]),
                        departure_minutes=self.parse_time_to_minutes(row["departure_time"]),
                        platform=platform,
                        track=track
                    )
                    
                    if s_id not in self.stop_departures:
                        self.stop_departures[s_id] = []
                    self.stop_departures[s_id].append(st)
                    
                    if t_id not in self.trip_sequences:
                        self.trip_sequences[t_id] = []
                    self.trip_sequences[t_id].append(st)
                except (ValueError, KeyError):
                    continue

        for t_id in self.trip_sequences:
            self.trip_sequences[t_id].sort(key=lambda x: x.stop_sequence)