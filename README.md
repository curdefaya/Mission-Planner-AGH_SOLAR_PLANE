# Autonomous Mission - Search & Precision Drop
**AGH Solar Plane 2026 – Zadanie rekrutacyjne**

Cześć! Opracowałem skrypt w Pythonie sterujący autonomiczną misją drona w symulacji SITL (Mission Planner). Ze względu na ograniczony czas, jaki mogłem poświęcić na zadanie, przygotowałem prosty i konkretny prototyp (Proof of Concept). Kod realizuje podstawowy przebieg misji zrzutu ładunku, choć posiada pewne uproszczenia, o których piszę poniżej.

---

## 1. Koncepcja i przebieg misji

Wybrałem scenariusz **Search & Precision Drop** :

1. **Start:** Dron przełącza się w tryb `GUIDED`, uzbraja silniki (`ARM`) i wznosi się na wysokość 15 m (`TAKEOFF`).
2. **Przelot:** Pętla nawigacyjna wysyła ramki `set_position_target_global_int_send`, kierując drona do punktu docelowego.
3. **Detekcja i kontrola odległości:** Dron na bieżąco przelicza dystans od celu (wzór Haversine).
4. **Precyzyjny zrzut:** Gdy dystans spadnie poniżej 4 m, skrypt wysyła sygnał PWM (2000 µs) na kanał 8 serwa (`MAV_CMD_DO_SET_SERVO`).
5. **Powrót:** Dron przełącza się w tryb `RTL` (Return-To-Launch) i wraca na miejsce startu.

---

## 2. Architektura i technologia

- **Język:** Python 3
- **Komunikacja:** `pymavlink` – natywna obsługa ramek MAVLink (TCP, port 5762).
- **Główne elementy (`main.py`):**
  - `get_distance_meters()` – obliczanie dystansu GPS.
  - Pętla nawigacyjna stale odświeżająca cel lotu (co zapobiega zatrzymywaniu się autopilota w GUIDED).
  - Wyzwalanie serwa zrzutowego za pomocą komendy MAVLink.

---

## 3. Jak uruchomić?

### Wymagania:
- Python 3.x
- Biblioteka `pymavlink` (`pip install pymavlink`)
- Mission Planner (z uruchomioną symulacją SITL)

### Krok po kroku:
1. Uruchom symulację SITL w Mission Plannerze. Upewnij się, że port TCP 5762 jest aktywny.
2. Uruchom skrypt:
   ```bash
   python main.py
   ```
3. Obserwuj przebieg lotu na mapie w Mission Plannerze oraz logi w konsoli.

---

## 4. Stan projektu, ograniczenia i wyzwania
- **Stan:** Kod działa, odpala się, realizuje założony przeze mnie program.

- **Prosta struktura proceduralna:** Kod to skrypt z głównym programem w main.py i scenariuszami w test_data/scenariusze_proste.py

---

## 5. Co dodałbym mając więcej czasu?

1. **Przebudowa na FSM:** Podział na jawne stany (`INIT`, `TAKEOFF`, `SEARCH`, `DROP`, `RTL`, `FAILSAFE`). **EDIT:** jawne stany są synchroniczne i zawiera je biblioteka mavlink, więc nie ma potrzeby dodania takiej maszyny to programu
2. **Asynchronous I/O (`asyncio`):** Odseparowanie pętli odczytu telemetrii MAVLink od pętli decyzyjnej. **EDIT:** Bibliotek mavlink tak jak pisałem wyżej jest synchroniczna i tak długo jak nie wysyłam danych do drona w trakcie jego lotu to dodawanie do programu asynchroniczności jest zbędne.
3. **Automatyczne testy jednostkowe (`unittest`):** Testowanie logiki bez konieczności uruchamiania pełnego SITL. **EDIT:** dodałem testy, na razie zawierają customową lokalizację do której leci dron. Postaram się dodać więcej customowych danych, przykładowo prędkość aby dron leciał szybciej gdy np. odległość jest większa niż 200 metrów.

## 6. Co dodałem i naprawiłem w tym tygodniu:

1. **Dodanie scenariuszy**: w tej chwilii scenariusze są 4 i zawierają różne lokalizacjie (1-blisko, 2-punkt (0.0), 3-dalsza lokalizacja, 4-customowa lokalizacja z danymi z terminala [lat,lon] w metrach)

2. **Naprawa zawieszania programu przy starcie i wysokości 15m**: dron nie wznosił się na 15 metrów przez zabezpieczenia, ardupilot ignorował przekazywane współrzędne geograficzne, żądanie telemetrii było nieprawidłowe i generalnie pętla while() nie miała sensu, bo zależała od ramek msg, które nie przychodziły. Aby to naprawić było trzeba zmusić program do wysyłania prawidłowo danych przez type_mask (maske bitową), aby komputer pokładowy nie ignorował tych danych.