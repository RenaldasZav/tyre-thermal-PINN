import mmap
import struct
import csv
import time
import os

# BEFORE EACH RUN: fill in these three values
RUN_BLOCK     = 1          # increment each variable change
TYRE_PRESSURE = 27.0       # psi
CAMBER        = -2.5       # degrees
TRACK_TEMP    = 25.0       # celsius

OUTPUT_FILE = "tyre_data.csv"
LOG_RATE_HZ = 50  #number of reads per second

# Each field is either int (i) or float (f), arrays use repeated f's
PHYSICS_STRUCT = struct.Struct(
    "<"        # little-endian
    "i"        # packetId
    "f"        # gas (throttle 0-1)
    "f"        # brake (0-1)
    "f"        # fuel
    "i"        # gear
    "i"        # rpms
    "f"        # steerAngle
    "f"        # speedKmh
    "3f"       # velocity [x, y, z]
    "3f"       # accG [x, y, z]
    "4f"       # wheelSlip [FL, FR, RL, RR]
    "4f"       # wheelLoad [FL, FR, RL, RR]  <- normal force (Fz)
    "4f"       # wheelsPressure [FL, FR, RL, RR]
    "4f"       # wheelAngularSpeed [FL, FR, RL, RR]
    "4f"       # tyreWear [FL, FR, RL, RR]
    "4f"       # tyreDirtyLevel [FL, FR, RL, RR]
    "4f"       # tyreCoreTemperature [FL, FR, RL, RR]  <- your target variable
    "4f"       # camberRAD [FL, FR, RL, RR]
    "4f"       # suspensionTravel [FL, FR, RL, RR]
    "f"        # drs
    "f"        # tc
    "f"        # heading
    "f"        # pitch
    "f"        # roll
    "f"        # cgHeight
    "10f"      # carDamage [5 zones x 2]
    "i"        # numberOfTyresOut
    "i"        # pitLimiterOn
    "f"        # abs
)

GRAPHICS_STRUCT_LAP_OFFSET = 4  
COMPLETED_LAPS_OFFSET = 4 + 4 + 4 + 4 + 4 + 4 + 68 #skipping straight to the data on which lap number im on

def read_completed_laps(graphics_map):
    graphics_map.seek(COMPLETED_LAPS_OFFSET)
    return struct.unpack("<i", graphics_map.read(4))[0]

def write_header(writer): #writing the top row of the CSV file
    writer.writerow([
        "timestamp",
        "run_block",
        "tyre_pressure_set",
        "camber_set",
        "track_temp_set",
        "lap_number",
        "speed_kmh",
        "throttle",
        "brake",
        "gear",
        "rpms",
        "steer_angle",
        # Lateral/longitudinal forces approximated from accG (g-forces)
        "long_accel_g",   # accG[2] - longitudinal
        "lat_accel_g",    # accG[0] - lateral
        # Wheel slip (proxy for tyre workload)
        "slip_FL", "slip_FR", "slip_RL", "slip_RR",
        # normal load per wheel (Fz)
        "load_FL", "load_FR", "load_RL", "load_RR",
        # tyre pressure
        "pressure_FL", "pressure_FR", "pressure_RL", "pressure_RR",
        # camber in radians
        "camber_FL", "camber_FR", "camber_RL", "camber_RR",
        # target variable - tyre core temperature
        "temp_FL", "temp_FR", "temp_RL", "temp_RR",
    ])

def main(): #status print
    print("=" * 50)
    print(f"  AC Tyre Logger")
    print(f"  Block: {RUN_BLOCK} | Pressure: {TYRE_PRESSURE} psi | Camber: {CAMBER}° | Track: {TRACK_TEMP}°C")
    print("=" * 50)
    print("Connecting to Assetto Corsa shared memory...")
    print("Make sure AC is running and you are in a session.\n")

    # Connect to AC shared memory
    try:
        physics_map  = mmap.mmap(0, 65536, "Local\\acpmf_physics",  access=mmap.ACCESS_READ)
        graphics_map = mmap.mmap(0, 65536, "Local\\acpmf_graphics", access=mmap.ACCESS_READ)
    except Exception as e:
        print(f"ERROR: Could not connect to AC shared memory.")
        print(f"Is Assetto Corsa running and are you loaded into a session?")
        print(f"Details: {e}")
        input("Press Enter to exit.")
        return

    print("Connected! Logging started. Press Ctrl+C to stop.\n")

    # Open CSV - append mode so multiple runs go into same file
    file_exists = os.path.exists(OUTPUT_FILE)
    csv_file = open(OUTPUT_FILE, "a", newline="")
    writer = csv.writer(csv_file)

    # Only write header if file is new
    if not file_exists:
        write_header(writer)

    interval = 1.0 / LOG_RATE_HZ
    rows_written = 0
    last_lap = -1

    try:
        while True:
            loop_start = time.time()

            physics_map.seek(0) #reading the physics data 
            raw = physics_map.read(PHYSICS_STRUCT.size)
            d = PHYSICS_STRUCT.unpack(raw)

            # Parse fields out of the unpacked tuple by position
            # Position index reference:
            # 0=packetId, 1=gas, 2=brake, 3=fuel, 4=gear, 5=rpms,
            # 6=steerAngle, 7=speedKmh, 8-10=velocity, 11-13=accG,
            # 14-17=wheelSlip, 18-21=wheelLoad, 22-25=wheelsPressure,
            # 26-29=wheelAngularSpeed, 30-33=tyreWear, 34-37=tyreDirtyLevel,
            # 38-41=tyreCoreTemperature, 42-45=camberRAD, 46-49=suspensionTravel
            # 50=drs, 51=tc, 52=heading, 53=pitch, 54=roll, 55=cgHeight,
            # 56-65=carDamage, 66=numberOfTyresOut, 67=pitLimiterOn, 68=abs

            lap = read_completed_laps(graphics_map)

            if lap != last_lap and last_lap != -1: #updating laps
                print(f"  Lap {lap} started")
            last_lap = lap

            writer.writerow([ #adds row to the CSV
                round(time.time(), 3),        # timestamp
                RUN_BLOCK,
                TYRE_PRESSURE,
                CAMBER,
                TRACK_TEMP,
                lap,
                round(d[7], 2),               # speed_kmh
                round(d[1], 3),               # throttle
                round(d[2], 3),               # brake
                d[4],                          # gear
                d[5],                          # rpms
                round(d[6], 4),               # steer_angle
                round(d[13], 4),              # long_accel_g (accG z)
                round(d[11], 4),              # lat_accel_g  (accG x)
                round(d[14], 4), round(d[15], 4), round(d[16], 4), round(d[17], 4),  # slip
                round(d[18], 2), round(d[19], 2), round(d[20], 2), round(d[21], 2),  # load
                round(d[22], 2), round(d[23], 2), round(d[24], 2), round(d[25], 2),  # pressure
                round(d[42], 4), round(d[43], 4), round(d[44], 4), round(d[45], 4),  # camber
                round(d[38], 2), round(d[39], 2), round(d[40], 2), round(d[41], 2),  # tyre temps
            ])

            rows_written += 1
            if rows_written % 500 == 0:
                csv_file.flush()  # save to disk every 500 rows
                print(f"  {rows_written} rows logged | Lap {lap} | {d[7]:.1f} km/h | "
                      f"Temps FL:{d[38]:.1f} FR:{d[39]:.1f} RL:{d[40]:.1f} RR:{d[41]:.1f} °C")

            # Sleep for remainder of interval to hit target Hz
            elapsed = time.time() - loop_start
            sleep_time = interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print(f"\nLogging stopped. {rows_written} rows written to '{OUTPUT_FILE}'.")

    finally:
        csv_file.flush()
        csv_file.close()
        physics_map.close()
        graphics_map.close()
        print("Files closed cleanly.")

if __name__ == "__main__":
    main()
