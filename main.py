import math
import time
from pymavlink import mavutil

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

            # Zapobiega zwieszeniu jak wskazuje 14.8m zamiast równo 15m (nie działa btw)
            if cur_alt >= 12.0 or (time.time() - start_time > 10.0):
                print("Wysokosc zaliczona, leci w trasie")
                break

    # Cel ~100m na polnoc od startu
    target_lat = home_lat + 0.0009
    target_lon = home_lon

    # set_position w petli, bo inaczej ArduPilot staje w miejscu
    while True:
        master.mav.set_position_target_global_int_send(
            0,
            master.target_system,
            master.target_component,
            mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,
            0b0000111111111000,
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