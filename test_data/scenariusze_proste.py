import math

def ask_for_shifts(home_lat: float = 52.2297):
    '''Pobieranie danych z terminala i przeliczanie na stopnie'''
    shift_lat_m = float(input("lat (m): "))
    shift_lon_m = float(input("lon (m): "))
    lat_shift_deg = shift_lat_m / 111139.0
    lon_shift_deg = shift_lon_m / (111139.0 * math.cos(math.radians(home_lat)))
    return {
        "name": f"Własne przesunięcie ({shift_lat_m}m lat, {shift_lon_m}m lon)",
        "home_lat_shift": lat_shift_deg,
        "home_lon_shift": lon_shift_deg,
    }


SCENARIOS = {
    1: {
        "name": "Przesunięcie w dodatnie szerokości i ujemne długości (+lat, -lon)",
        "home_lat_shift": 0.0018,
        "home_lon_shift": -0.0008,
    },
    2: {
        "name": "Brak przesunięcia",
        "home_lat_shift": 0.0,
        "home_lon_shift": 0.0,
    },
    3: {
        "name": "Duże przesunięcie na południowy zachód (-lat, -lon)",
        "home_lat_shift": -0.0150,
        "home_lon_shift": -0.0220,
    },
    4: {
        "name": "Przesunięcie wskazane przez użytkownika w metrach (lat, lon)",
        "action": ask_for_shifts 
    }
}

def get_sample(scenario_id: int = 1) -> dict:
    """Zwraca dane dla wybranego scenariusza. Domyślnie scenariusz 1."""
    scenario = SCENARIOS.get(scenario_id, SCENARIOS[1])
    if "action" in scenario:
        return scenario["action"]()
    return scenario