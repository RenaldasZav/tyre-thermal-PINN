import ac
import acsys
import os
import csv
import time

# ─────────────────────────────────────────────
RUN_BLOCK     = 1
TYRE_PRESSURE = 20.0
CAMBER        = -2.5
TRACK_TEMP    = 25.0
# ─────────────────────────────────────────────

app_window   = 0
label        = 0
timer        = 0
csv_file     = None
writer       = None
rows_written = 0
initialized  = False

def acMain(ac_version):
    global app_window, label, csv_file, writer, initialized

    try:
        app_window = ac.newApp("tyre_logger")
        ac.setSize(app_window, 200, 50)
        label = ac.addLabel(app_window, "Tyre Logger: Starting...")

        output = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "tyre_data.csv"
        )

        file_exists = os.path.exists(output)
        csv_file = open(output, "a", newline="")
        writer = csv.writer(csv_file)

        if not file_exists:
            writer.writerow([
                "timestamp","run_block","tyre_pressure_set","camber_set",
                "track_temp_set","lap_number","speed_kmh","throttle","brake",
                "gear","rpms","steer_angle","long_accel_g","lat_accel_g",
                "slip_FL","slip_FR","slip_RL","slip_RR",
                "load_FL","load_FR","load_RL","load_RR",
                "pressure_FL","pressure_FR","pressure_RL","pressure_RR",
                "camber_FL","camber_FR","camber_RL","camber_RR",
                "temp_FL","temp_FR","temp_RL","temp_RR"
            ])

        initialized = True
        ac.setText(label, "Tyre Logger: Running")
        ac.log("tyre_logger: acMain OK")

    except Exception as e:
        ac.log("tyre_logger: acMain ERROR - " + str(e))

    return "tyre_logger"

def acUpdate(deltaT):
    global timer, rows_written, csv_file, writer, initialized

    if not initialized:
        return

    timer += deltaT
    if timer < 0.02:
        return
    timer = 0

    try:
        speed    = ac.getCarState(0, acsys.CS.SpeedKMH)
        throttle = ac.getCarState(0, acsys.CS.Gas)
        brake    = ac.getCarState(0, acsys.CS.Brake)
        gear     = ac.getCarState(0, acsys.CS.Gear)
        rpms     = ac.getCarState(0, acsys.CS.RPM)
        steer    = ac.getCarState(0, acsys.CS.Steer)
        lap      = ac.getCarState(0, acsys.CS.LapCount)
        accG     = ac.getCarState(0, acsys.CS.AccG)
        slip     = ac.getCarState(0, acsys.CS.NdSlip)
        load     = ac.getCarState(0, acsys.CS.Load)
        pressure = ac.getCarState(0, acsys.CS.DynamicPressure)
        camber_w = ac.getCarState(0, acsys.CS.CamberRad)
        temps    = ac.getCarState(0, acsys.CS.CurrentTyresCoreTemp)

        writer.writerow([
            round(time.time(), 3), RUN_BLOCK, TYRE_PRESSURE, CAMBER, TRACK_TEMP,
            lap, round(speed, 2), round(throttle, 3), round(brake, 3),
            gear, round(rpms, 1), round(steer, 4),
            round(accG[2], 4), round(accG[0], 4),
            round(slip[0], 4), round(slip[1], 4), round(slip[2], 4), round(slip[3], 4),
            round(load[0], 2), round(load[1], 2), round(load[2], 2), round(load[3], 2),
            round(pressure[0], 2), round(pressure[1], 2), round(pressure[2], 2), round(pressure[3], 2),
            round(camber_w[0], 4), round(camber_w[1], 4), round(camber_w[2], 4), round(camber_w[3], 4),
            round(temps[0], 2), round(temps[1], 2), round(temps[2], 2), round(temps[3], 2)
        ])

        rows_written += 1

        if rows_written % 500 == 0:
            csv_file.flush()
            ac.setText(label, "Logged: " + str(rows_written) + " rows")
            ac.log("tyre_logger: " + str(rows_written) + " rows written")

    except Exception as e:
        ac.log("tyre_logger: acUpdate ERROR - " + str(e))

def acShutdown():
    global csv_file
    try:
        if csv_file:
            csv_file.flush()
            csv_file.close()
            ac.log("tyre_logger: shutdown OK")
    except Exception as e:
        ac.log("tyre_logger: shutdown ERROR - " + str(e))
