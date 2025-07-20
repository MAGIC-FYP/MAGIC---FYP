"""
Actual piece detection code.
Still work in progress!

Notes: 
- Logic may need to be updated as if piece is picked up and placed 5 seconds later it won't register as 1 move.

- No logic for the sensor on the electromagnet
"""

import time
import board
import busio
import RPi.GPIO as GPIO  # Assuming Raspberry Pi for GPIO control
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# --------------------------
# INITIAL SETUP
# --------------------------

# I2C setup
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)

# ADS1115 analog input (shared between MUX outputs)
adc_channel = AnalogIn(ads, ADS.P0)  # Assuming all MUXes feed into A0

# GPIO pin setup for multiplexer
S0, S1, S2, S3 = 13, 14, 15, 16  # GPIO pins
MUX_ENABLE_PINS = [17,18, 19, 20, 21]  # Enable pins for MUX1E–MUX6E 

GPIO.setmode(GPIO.BCM)
GPIO.setup([S0, S1, S2, S3] + MUX_ENABLE_PINS, GPIO.OUT)

# --------------------------
# GLOBAL CONFIG
# --------------------------

NUM_SENSORS = 96    # Will be changed  
sensor_states = [0.0] * NUM_SENSORS  # Initial baseline state

# --------------------------
# HELPER FUNCTIONS
# --------------------------

# This finds the max and minimum sensor voltages 
def cali_sensor(mux_channels_with_magnet, mux_channels_without_magnet, mux_select_fn, ads_read_fn):
    magnet_vals = []
    no_magnet_vals = []

    # Read values for channels with magnet (expected HIGH)
    for channel in mux_channels_with_magnet:
        mux_select_fn(channel)
        time.sleep(0.01)  # small delay for stability
        val = ads_read_fn()
        magnet_vals.append(val)

    # Read values for channels without magnet (expected LOW)
    for channel in mux_channels_without_magnet:
        mux_select_fn(channel)
        time.sleep(0.01)
        val = ads_read_fn()
        no_magnet_vals.append(val)

    # Compute averages
    avg_on = sum(magnet_vals) / len(magnet_vals)
    avg_off = sum(no_magnet_vals) / len(no_magnet_vals)

    # Apply ±5% buffer
    lower_thresh = avg_off + 0.05
    upper_thresh = avg_on - 0.05

    return lower_thresh, upper_thresh

def sensor_index_to_square(index):  # Converts sensor number to chess location
    total_cols = 12  # 2 graveyard cols + 8 board cols + 2 graveyard cols
    row = index // total_cols
    col = index % total_cols

    # Unsure what to name graveyard squares. Currently set as GY W/B XX - GraveYard White/Black [col][row]
    if col < 2:
        gy_col = chr(ord('A') + col)
        return f"GYW[{gy_col}][{row}]"
    elif 2 <= col < 10: # Normal chess square 
        board_col = chr(ord('a') + (col - 2))
        return f"{board_col}{row + 1}"
    else:
        gy_col = chr(ord('A') + (col - 10))
        return f"GYB[{gy_col}][{row}]"

def select_mux_channel(channel):
    # Set S0–S3 for the channel (0–15)
    GPIO.output(S0, channel & 0x01)
    GPIO.output(S1, (channel >> 1) & 0x01)
    GPIO.output(S2, (channel >> 2) & 0x01)
    GPIO.output(S3, (channel >> 3) & 0x01)

def enable_mux(index):
    # Enable one MUX at a time (active LOW)
    for i, pin in enumerate(MUX_ENABLE_PINS):
        GPIO.output(pin, GPIO.LOW if i == index else GPIO.HIGH)

def read_all_sensors():
    sensor_values = []
    for mux_index in range(6):  # 6 MUX chips × 16 channels = 96 sensors
        enable_mux(mux_index)
        for ch in range(16):
            select_mux_channel(ch)
            time.sleep(0.001)  # Let signal settle
            sensor_values.append(adc_channel.voltage)
    return sensor_values

def detect_changes(old_state, new_state, thresholds):
    changes = []
    for i in range(NUM_SENSORS):
        if abs(old_state[i] - new_state[i]) > thresholds[i]:
            square = sensor_index_to_square(i)
            change_type = "removed" if new_state[i] < old_state[i] else "placed"
            changes.append((square, change_type))
    return changes

# --------------------------
# MAIN LOOP
# --------------------------

print("Calibrating initial sensor state...")
previous_state = read_all_sensors()
print("Calibration complete. Monitoring for changes...\n")

while True:
    time.sleep(0.1)  # Adjust as needed
    current_state = read_all_sensors()
    changes = detect_changes(previous_state, current_state)

    if changes:
        print("Detected changes:")
        for square, action in changes:
            print(f"  Piece {action} on {square}")
        print()

    previous_state = current_state.copy()


'''
Possible logic fix:

pending_removal = None

for square, action in changes:
    if action == "removed":
        pending_removal = square
    elif action == "placed" and pending_removal:
        print(f"Moved from {pending_removal} to {square}")
        pending_removal = None

Only time this could crash is during setup as multiple pieces are moving
'''



