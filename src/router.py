import heapq
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from src.loader import GTFSLoader
from src.models import RouteLeg, StopTime, CompleteJourney

class GTFSRouter:
    def __init__(self, loader: GTFSLoader):
        self.loader = loader

    def find_all_routes_24h(self, start_stop_id: str, end_stop_id: str) -> List[CompleteJourney]:
        now = datetime.now()
        start_date_str = now.strftime("%Y%m%d")
        start_time_minutes = now.hour * 60 + now.minute

        routes: List[CompleteJourney] = []
        current_offset_minutes = 0
        MAX_24H_MINUTES = 1440
        seen_trips: set[Tuple[str, int]] = set()

        while current_offset_minutes < MAX_24H_MINUTES:
            journey = self._find_single_route_absolute(
                start_stop_id, end_stop_id, start_date_str, start_time_minutes, current_offset_minutes
            )
            
            if not journey:
                break
                
            first_leg = journey.legs[0]
            dep_absolute = first_leg.departure_minutes_absolute
            
            if dep_absolute >= MAX_24H_MINUTES:
                break

            trip_key = (first_leg.trip.id, dep_absolute)
            if trip_key not in seen_trips:
                routes.append(journey)
                seen_trips.add(trip_key)
            
            current_offset_minutes = dep_absolute + 1

        return routes

    def _find_single_route_absolute(self, start_stop_id: str, end_stop_id: str, 
                                    start_date_str: str, start_time_minutes: int, 
                                    current_offset_minutes: int) -> CompleteJourney | None:
        base_search_time_absolute = current_offset_minutes
        pq: List[Tuple[int, str]] = [(base_search_time_absolute, start_stop_id)]
        best_arrival: Dict[str, int] = {start_stop_id: base_search_time_absolute}
        parent_legs: Dict[str, Tuple[StopTime, StopTime, int, int]] = {}

        MIN_TRANSFER_MINUTES = 5
        base_date = datetime.strptime(start_date_str, "%Y%m%d")

        while pq:
            curr_time_abs, curr_stop = heapq.heappop(pq)

            if curr_stop == end_stop_id:
                break

            if curr_time_abs > best_arrival.get(curr_stop, curr_time_abs):
                continue

            total_minutes_from_start_of_today = start_time_minutes + curr_time_abs
            days_offset = total_minutes_from_start_of_today // 1440
            current_day_minutes = total_minutes_from_start_of_today % 1440
            current_eval_date = (base_date + timedelta(days=days_offset)).strftime("%Y%m%d")

            for departure_st in self.loader.stop_departures.get(curr_stop, []):
                trip = self.loader.trips[departure_st.trip_id]
                active_days = self.loader.calendar_services.get(trip.service_id, set())
                if current_eval_date not in active_days:
                    continue

                required_dep_minutes_in_day = current_day_minutes
                if curr_stop != start_stop_id:
                    required_dep_minutes_in_day += MIN_TRANSFER_MINUTES

                if departure_st.departure_minutes < required_dep_minutes_in_day:
                    continue

                dep_time_abs = (days_offset * 1440) + departure_st.departure_minutes - start_time_minutes

                trip_stops = self.loader.trip_sequences[departure_st.trip_id]
                for arrival_st in trip_stops:
                    if arrival_st.stop_sequence > departure_st.stop_sequence:
                        dest_stop = arrival_st.stop_id
                        arr_time_abs = (days_offset * 1440) + arrival_st.arrival_minutes - start_time_minutes
                        
                        if arr_time_abs < best_arrival.get(dest_stop, 999999):
                            best_arrival[dest_stop] = arr_time_abs
                            parent_legs[dest_stop] = (departure_st, arrival_st, dep_time_abs, arr_time_abs)
                            heapq.heappush(pq, (arr_time_abs, dest_stop))

        if end_stop_id not in best_arrival:
            return None

        legs: List[RouteLeg] = []
        curr = end_stop_id
        while curr in parent_legs:
            dep_st, arr_st, dep_abs, arr_abs = parent_legs[curr]
            trip = self.loader.trips[dep_st.trip_id]
            
            leg = RouteLeg(
                trip=trip,
                from_stop_id=dep_st.stop_id,
                to_stop_id=arr_st.stop_id,
                # Wykorzystanie nowej metody naprawiającej dziwne godziny (np. 24:30 -> 00:30)
                departure_time_str=self.loader.format_minutes_to_clock_time(dep_st.departure_minutes),
                arrival_time_str=self.loader.format_minutes_to_clock_time(arr_st.arrival_minutes),
                departure_minutes_absolute=dep_abs,
                arrival_minutes_absolute=arr_abs,
                duration_minutes=arr_st.arrival_minutes - dep_st.departure_minutes,
                from_platform=dep_st.platform,
                from_track=dep_st.track,
                to_platform=arr_st.platform,
                to_track=arr_st.track
            )
            legs.insert(0, leg)
            curr = dep_st.stop_id

        return CompleteJourney(legs=legs)