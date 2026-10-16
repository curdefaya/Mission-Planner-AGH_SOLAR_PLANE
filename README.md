# Autonomous Mission - Search & Precision Drop
**AGH Solar Plane 2026 – Zadanie rekrutacyjne**

Cześć! Opracowałem skrypt w Pythonie sterujący autonomiczną misją drona w symulacji SITL (Mission Planner). Ze względu na ograniczony czas, jaki mogłem poświęcić na zadanie, przygotowałem prosty i konkretny prototyp (Proof of Concept). Kod realizuje podstawowy przebieg misji zrzutu ładunku, choć posiada pewne uproszczenia, o których szczerze piszę poniżej.

---

## 1. Koncepcja i przebieg misji

Wybrałem scenariusz **Search & Precision Drop** (poszukiwanie i zrzut ładunku):

1. **Start:** Dron przełącza się w tryb `GUIDED`, uzbraja silniki (`ARM`) i wznosi się na wysokość 15 m (`TAKEOFF`).
2. **Przelot:** Pętla nawigacyjna wysyła ramki `set_position_target_global_int_send`, kierując drona do punktu docelowego (~100 m na północ od miejsca startu).
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

## 4. Stan projektu, ograniczenia i wyzwania (Szczerze o projekcie)

Ze względu na brak czasu nie zdążyłem rozbudować projektu do pełnej wersji:

- **Cel wyznaczany statycznie:** Pozycja celu jest wyliczana prostym przesunięciem geograficznym (`home_lat + 0.0009`).
- **Prosta struktura proceduralna:** Kod jest jednoplikowym skryptem. Przy większej ilości czasu zastosowałbym pełny FSM.
- **Problem z wysokością** W symulacji odczyt wysokości i ramek GPS bywa nieidealny (np. dron wznosi się do 14.8 m i potrafi się przywiesić w pętli oczekiwania). Aktualnie nie wiem jak to naprawić, ale gdybym miał czas w najbliższy weekend to mógłbym się tym zająć.

---

## 5. Co dodałbym mając więcej czasu?

1. **Przebudowa na FSM:** Podział na jawne stany (`INIT`, `TAKEOFF`, `SEARCH`, `DROP`, `RTL`, `FAILSAFE`).
2. **Asynchronous I/O (`asyncio`):** Odseparowanie pętli odczytu telemetrii MAVLink od pętli decyzyjnej.
3. **Automatyczne testy jednostkowe (`unittest`):** Testowanie logiki bez konieczności uruchamiania pełnego SITL.
