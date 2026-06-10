import sys
from datetime import datetime
from src.loader import GTFSLoader
from src.router import GTFSRouter

class GTFSConsoleApp:
    def __init__(self, data_dir: str):
        self.loader = GTFSLoader(data_dir)
        self.router = None

    def bootstrap(self) -> bool:
        print("[⚡] Parsowanie zbiorów danych i weryfikacja peronów GTFS PKP PLK...")
        start_time = datetime.now()
        try:
            self.loader.load()
            self.router = GTFSRouter(self.loader)
            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"[✓] Załadowano pomyślnie w bazie RAM w czasie {elapsed:.2f}s.")
            print(f"    Węzły stacyjne: {len(self.loader.stops)} | Czynne pociągi: {len(self.loader.trips)}")
            return True
        except Exception as e:
            print(f"[❌] Błąd krytyczny ładowania danych rozkładu: {e}", file=sys.stderr)
            return False

    def start_loop(self) -> None:
        print("\n" + "=" * 120)
        print(" AUTOMATYCZNA TABLICA ODJAZDÓW Z LOKALIZACJĄ (PERON/TOR) — NAJBLIŻSZE 24 GODZINY OD TERAZ")
        print(" Wyjście z programu: wpisz 'q' lub 'exit'")
        print("=" * 120)

        while True:
            try:
                start_name = input("\nStacja początkowa: ").strip()
                if start_name.lower() in ['q', 'exit']: break
                
                end_name = input("Stacja docelowa: ").strip()
                if end_name.lower() in ['q', 'exit']: break

                start_id = self.loader.stop_name_to_id.get(start_name.lower())
                end_id = self.loader.stop_name_to_id.get(end_name.lower())

                if not start_id:
                    print(f"[-] Nie odnaleziono stacji w bazie PLK: '{start_name}'")
                    continue
                if not end_id:
                    print(f"[-] Nie odnaleziono stacji w bazie PLK: '{end_name}'")
                    continue

                current_time_str = datetime.now().strftime("%H:%M")
                print(f"[.] Pobieranie połączeń na 24h od aktualnej godziny systemowej {current_time_str}...")
                
                raw_journeys = self.router.find_all_routes_24h(start_id, end_id)

                if not raw_journeys:
                    print("[!] Brak dostępnych połączeń w przeciągu najbliższych 24 godzin.")
                    continue

                # --- INTELIGENTNE FILTROWANIE ANOMALII CZASOWYCH (DLA BLISKICH STACJI) ---
                min_duration = min(j.total_duration for j in raw_journeys)
                
                filtered_journeys = []
                for j in raw_journeys:
                    is_direct = len(j.legs) == 1
                    
                    if min_duration <= 15:
                        if not is_direct and j.total_duration > min_duration * 3:
                            continue
                        if j.total_duration > 45:
                            continue
                    else:
                        if j.total_duration > max(min_duration * 2, min_duration + 60):
                            continue
                            
                    filtered_journeys.append(j)
                # -----------------------------------------------------------------------------

                if not filtered_journeys:
                    print("[!] Brak rozsądnych czasowo połączeń w przeciągu najbliższych 24 godzin.")
                    continue

                print(f"\n[✓] ZNALEZIONO {len(filtered_journeys)} DOSTĘPNYCH KURSÓW (odfiltrowano połączenia okrężne):")
                print("=" * 135)
                print(f" {'Lp.':<4} | {'Odjazd':<6} | {'Przyjazd':<8} | {'Czas':<8} | {'Przebieg trasy (Numer pociągu, Stacje, Perony i Tory)':<65}")
                print("-" * 135)
                
                for idx, journey in enumerate(filtered_journeys, 1):
                    route_details = []
                    for leg in journey.legs:
                        p_num = leg.trip.train_number
                        f_st = self.loader.stops[leg.from_stop_id].name
                        t_st = self.loader.stops[leg.to_stop_id].name
                        
                        # Odporne formatowanie informacji o peronie i torze
                        if leg.from_platform != "-" and leg.from_track != "-":
                            plat_track_info = f"(Per. {leg.from_platform}, Tor {leg.from_track})"
                        elif leg.from_platform != "-":
                            plat_track_info = f"(Per. {leg.from_platform})"
                        elif leg.from_track != "-":
                            plat_track_info = f"(Tor {leg.from_track})"
                        else:
                            plat_track_info = ""
                            
                        route_details.append(f"[{p_num}] {f_st} {plat_track_info} -> {t_st}")
                    
                    route_str = "  [PRZESIADKA]  ".join(route_details)
                    duration_str = f"{journey.total_duration} min"
                    
                    print(f" {idx:<4} | {journey.departure_time_str:<6} | {journey.arrival_time_str:<8} | {duration_str:<8} | {route_str}")
                    
                print("=" * 135)

            except (KeyboardInterrupt, EOFError):
                print("\nZamykanie aplikacji. Bezpiecznej podróży!")
                break