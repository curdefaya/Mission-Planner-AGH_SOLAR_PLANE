import math
import time
from pymavlink import mavutil
from test_data.scenariusze_proste import SCENARIOS, get_sample

# SITL po TCP z MP
CONNECTION_STRING = "tcp:127.0.0.1:5762"


def get_distance_meters(lat1, lon1, lat2, lon2):
    R = 6371000.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def main():
    print("Laczymy z SITLem...")
    master = mavutil.mavlink_connection(CONNECTION_STRING)
    master.wait_heartbeat()
    print("Dziala")

    master.mav.request_data_stream_send(
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_DATA_STREAM_POSITION,
        10,  # Częstotliwość w Hz
        1,   # Włączenie strumienia (1 = ON, 0 = OFF)
    )

    print("=== WYBÓR SCENARIUSZA TESTOWEGO ===")
    for key, data in SCENARIOS.items():
        print(f"[{key}] {data['name']}")
    
    user_input = input("\nWybierz numer scenariusza (1-4): ")
    
    try:
        scenario_id = int(user_input)
    except ValueError:
        print("Nieprawidłowy wybór, wczytuję domyślny scenariusz [1].")
        scenario_id = 1

    test_data = get_sample(scenario_id)
    
    print("\n[Wczytane dane testowe]:")
    print(f"lat_shift: {test_data['home_lat_shift']}")
    print(f"lon_shift: {test_data['home_lon_shift']}")


    # GUIDED
    mode_id = master.mode_mapping().get("GUIDED")
    master.mav.set_mode_send(
        master.target_system,
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
        mode_id,
    )
    time.sleep(0.5)

    # Armujemy puszke
    print("Uzbrajanie...")
    master.mav.command_long_send(
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
        0,
        1,
        0,
        0,
        0,
        0,
        0,
        0,
    )
    master.motors_armed_wait()
    print("Uzbrojony, mozna leciec")

    # Startujemy na 15m
    target_alt = 15.0
    print(f"Lecimy w gore na {target_alt}m...")
    master.mav.command_long_send(
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        target_alt,
    )

    home_lat, home_lon = None, None
    start_time = time.time()

    # Czekamy az sie wzniesie (albo strzeli timeout)
    while True:

        if time.time() - start_time > 15.0:
            print("Timeout startu")
            break
        
        msg = master.recv_match(
            type="GLOBAL_POSITION_INT", blocking=True, timeout=0.5 
        )
        if msg:
            cur_alt = msg.relative_alt / 1000.0
            cur_lat = msg.lat / 1e7
            cur_lon = msg.lon / 1e7

            if home_lat is None:
                home_lat, home_lon = cur_lat, cur_lon

            print(f"Alt: {cur_alt:.1f}m / {target_alt}m")

            # Zapobiega zwieszeniu jak wskazuje 14.8m zamiast równo 15m (już działa btw)
            if cur_alt >= (target_alt * 0.95):
                print("Wysokosc zaliczona, leci w trasie")
                break
    if home_lat is None:
        print("Blad: nie odebrano wspolrzednych home_lat")
        return

    # Cel z wczytanego scenariusza
    target_lat = home_lat + test_data["home_lat_shift"]
    target_lon = home_lon + test_data['home_lon_shift']

    '''
    type_mask = (
             mavutil.mavlink.POSITION_TARGET_TYPEMASK_X_IGNORE |
             mavutil.mavlink.POSITION_TARGET_TYPEMASK_Y_IGNORE |
             mavutil.mavlink.POSITION_TARGET_TYPEMASK_Z_IGNORE |
             mavutil.mavlink.POSITION_TARGET_TYPEMASK_VX_IGNORE |  # Set to IGNORE to control, clear to ignore? 
             # Correction: In MAVLink, 1=Ignore, 0=Control. 
             # So to control VX, we do NOT set the IGNORE bit.
             # To ignore VX, we DO set the IGNORE bit.
             
             # Example: Control VX, VY, VZ. Ignore everything else.
             mavutil.mavlink.POSITION_TARGET_TYPEMASK_AX_IGNORE |
             mavutil.mavlink.POSITION_TARGET_TYPEMASK_AY_IGNORE |
             mavutil.mavlink.POSITION_TARGET_TYPEMASK_AZ_IGNORE |
             mavutil.mavlink.POSITION_TARGET_TYPEMASK_YAW_IGNORE |
             mavutil.mavlink.POSITION_TARGET_TYPEMASK_YAW_RATE_IGNORE)
    '''

    type_mask = 0b0000110111111000

    # set_position w petli, bo inaczej ArduPilot staje w miejscu
    while True:
        master.mav.set_position_target_global_int_send(
            0,
            master.target_system,
            master.target_component,
            mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,
            type_mask,
            int(target_lat * 1e7),
            int(target_lon * 1e7),
            float(target_alt),
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        )

        msg = master.recv_match(
            type="GLOBAL_POSITION_INT", blocking=True, timeout=0.5
        )
        if msg:
            cur_lat = msg.lat / 1e7
            cur_lon = msg.lon / 1e7
            dist = get_distance_meters(cur_lat, cur_lon, target_lat, target_lon)
            print(f"Dystans do celu: {dist:.1f}m")

            if dist < 4.0:
                print("Jestesmy na miejscu, zrzut")
                break

        time.sleep(0.1)

    # Zrzut paczki serwem na kanale 8
    master.mav.command_long_send(
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_CMD_DO_SET_SERVO,
        0,
        8,
        2000,
        0,
        0,
        0,
        0,
        0,
    )
    print("Poszedl ladunek")
    time.sleep(2)

    # Powrót do bazy
    print("BAZA (RTL)")
    rtl_mode_id = master.mode_mapping().get("RTL")
    master.mav.set_mode_send(
        master.target_system,
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
        rtl_mode_id,
    )
    print("Koniec.")


if __name__ == "__main__":
    main()