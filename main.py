import os
from src.cli import GTFSConsoleApp

def main():
    # Pobieranie ścieżki do folderu 'data', w którym znajdują się Twoje pliki tekstowe
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_directory = os.path.join(base_dir, "data")
    
    # Podstawowa walidacja obecności krytycznych struktur przed uruchomieniem
    critical_files = ["stops.txt", "trips.txt", "stop_times.txt", "calendar_dates.txt"]
    missing = [f for f in critical_files if not os.path.exists(os.path.join(data_directory, f))]
    
    if missing:
        print(f"BŁĄD: W katalogu '{data_directory}' brakuje wymaganych plików GTFS: {missing}")
        print("Upewnij się, że przeniosłeś tam wypakowane pliki tekstowe.")
        return

    app = GTFSConsoleApp(data_directory)
    if app.bootstrap():
        app.start_loop()

if __name__ == "__main__":
    main()