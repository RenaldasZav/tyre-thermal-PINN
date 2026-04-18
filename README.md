# tyre-thermal-PINN
Physics-informed neural network for predicting tyre thermal behaviour using Assetto Corsa telemetry data

# Project Overview
The purpose of this project is to create a PINN to model the relationship between driving inputs, setup parameters, and tyre core temps. The PINN will incorporate governing physics equations directly into the loss function allowing for accurate predicitons with limited data.

# Data Acquisition
Telemetry data is collected from Assetto Corsa. The logger runs alongside the game and records data at 50Hz.

**Car:** Mercedes AMG GT3 (2015)  
**Track:** Imola  
**Features logged:**
- Lateral and longitudinal g-forces
- Wheel slip per corner
- Normal load per corner (Fz)
- Tyre pressure per corner
- Camber per corner
- Speed, throttle, brake, steering angle
- **Target variable:** Tyre core temperature per corner (FL, FR, RL, RR)

Baseline setup, 4 laps per configuration, no tyre blankets, one variable changed per 4 lap run.
