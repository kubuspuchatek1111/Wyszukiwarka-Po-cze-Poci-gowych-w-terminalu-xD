# 🚄 GTFS PKP PLK Router & Departure Board

Konsolowa aplikacja w języku Python służąca do wyszukiwania połączeń kolejowych w oparciu o otwarte zbiory danych **GTFS (General Transit Feed Specification)** dostarczane przez PKP Polskie Linie Kolejowe S.A. 

Aplikacja ładuje pełny rozkład jazdy do pamięci RAM, automatycznie naprawia specyficzne błędy w formatowaniu danych peronowych i torowych oraz udostępnia interaktywną tablicę odjazdów na najbliższe 24 godziny z inteligentnym filtrowaniem tras okrężnych.

## ✨ Kluczowe funkcje

### 1. 🛠️ Zaawansowana sanityzacja danych Peron/Tor (Cross-Validation)
Oficjalne bazy danych PKP PLK bardzo często zawierają anomalie w numeracji torów i peronów. Ten system posiada wbudowany moduł heurystyczny w klasie `GTFSLoader`, który automatycznie wykrywa i naprawia następujące patologie danych:
* **Format `[peron][tor]` (sklejony):** Gdy `platform="12"` i `track="-"`, system automatycznie rozdziela to na **Peron 1, Tor 2**.
* **Format `[tor][peron]` (odwrócony sklejony):** Gdy `platform="-"` i `track="12"`, system konwertuje to na **Peron 1, Tor 2**.
* **Duplikacja peronu w numerze toru:** Gdy `platform="1"` i `track="12"`, algorytm ucina pierwszą cyfrę, zwracając **Tor 2**.
* **Duplikacja toru w numerze peronu:** Gdy `platform="2"`, a `track="12"`, system wykrywa zgodność drugiej cyfry i koryguje dane do postaci **Peron 2, Tor 1** (częsta anomalia np. na stacji Pilawa).
* **Bezpieczeństwo dużych stacji:** Algorytm ignoruje tory prawdziwie dwucyfrowe (np. Warszawa Wschodnia, Peron 7, Tor 21), ponieważ numery te nie wykazują fałszywej korelacji krzyżowej z numerem peronu.

### 2. 🧠 Inteligentne filtrowanie anomalii czasowych
Podczas wyszukiwania połączeń przesiadkowych na bliskich odległościach, standardowe algorytmy routingu potrafią zaproponować nielogiczne, kilkugodzinne podróże okrężne. System automatycznie oblicza najkrótszy możliwy czas podróży dla danej relacji i odsiewa połączenia, które drastycznie przekraczają ten próg (np. blokuje 3-godzinne podróże przesiadkowe dla stacji oddalonych o 15 minut drogi).

### 3. 🕒 Normalizacja czasu 24h+
System radzi sobie z zapisem kursów nocnych w standardzie GTFS (gdzie godziny po północy zapisywane są np. jako `25:30`) i bezbłędnie normalizuje je do standardowego formatu zegarowego (`01:30`).

---

## 📂 Struktura projektu

```text
.
├── data/                      # Katalog ze skompresowanymi/rozpakowanymi plikami GTFS
│   ├── agency.txt
│   ├── calendar_dates.txt
│   ├── routes.txt
│   ├── stop_times.txt
│   ├── stops.txt
│   └── trips.txt
├── src/
│   ├── __init__.py
│   ├── cli.py                 # Interfejs konsolowy, pętla główna i filtry tras
│   ├── loader.py              # Parser plików GTFS i silnik sanityzacji danych
│   ├── models.py              # Klasy danych (Stop, Trip, StopTime, Journey, Leg)
│   └── router.py              # Algorytm wyszukiwania tras przesiadkowych na 24h
├── main.py                    # Główny punkt wejścia (skrypt uruchomieniowy)
└── README.md                  # Dokumentacja projektu
## 🚀 Instrukcja uruchomienia i konfiguracji

Projekt został zaprojektowany z myślą o minimalizmie — **nie wymaga instalowania żadnych zewnętrznych bibliotek (Zero Dependencies)**. Wykorzystuje wyłącznie wbudowaną bibliotekę standardową języka Python.

### 1. Wymagania systemowe
* **Python:** Wersja `3.8` lub nowsza.
* **System operacyjny:** Windows, macOS lub Linux.

---

### 2. Przygotowanie struktury plików
Upewnij się, że pliki projektu są ułożone w następujący sposób. Kluczowe jest utworzenie folderu `data/` i umieszczenie w nim rozpakowanych plików `.txt` z paczki GTFS:

```text
twój-projekt/
├── data/                      <-- UTWÓRZ TEN FOLDER
│   ├── calendar_dates.txt
│   ├── stop_times.txt
│   ├── stops.txt
│   └── trips.txt
├── src/
│   ├── __init__.py
│   ├── cli.py
│   ├── loader.py
│   ├── models.py
│   └── router.py
└── main.py                    <-- Główny plik uruchomieniowy
