"""
Created: 15/09/25
Piece detection control for the continous board using 4x 16-channel multiplexers and an ADS1115 ADC.

This file should create a heat map showing which sensors on the board are detecting the magnet.
"""

import time
import board
import busio
import RPi.GPIO as GPIO  # Assuming Raspberry Pi for GPIO control
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# --------------------------
# INITIAL SETUP
# --------------------------

# I2C setup
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)

# Define ADC channels for each mux
adc_channels = [
    AnalogIn(ads, ADS.P0),  # MUX1
    AnalogIn(ads, ADS.P1),  # MUX2
    AnalogIn(ads, ADS.P2),  # MUX3
    AnalogIn(ads, ADS.P3)   # MUX4
]

# GPIO pin setup
S0, S1, S2, S3 = 22, 23, 24, 25  # MUX select pins for all 4 muxes
MUX_ENABLE = 5

GPIO.setmode(GPIO.BCM)

# Setup select pins
GPIO.setup([S0, S1, S2, S3], GPIO.OUT)

# Setup and enable muxes (active LOW)
GPIO.setup(MUX_ENABLE, GPIO.OUT)
GPIO.output(MUX_ENABLE, GPIO.LOW)

NUM_SENSORS = 64
NUM_ROWS = 8
NUM_COLS = 8

# --------------------------
# HELPER FUNCTIONS
# --------------------------
def select_mux_channel(channel):
    """Set S0-S3 to pick a mux channel 0-15."""
    GPIO.output(S0, channel & 0x01)
    GPIO.output(S1, (channel >> 1) & 0x01)
    GPIO.output(S2, (channel >> 2) & 0x01)
    GPIO.output(S3, (channel >> 3) & 0x01)

def read_all_sensors():
    """Read all 64 sensors (4 muxes x 16 channels)."""
    sensor_values = []
    for ch in range(16):
        select_mux_channel(ch)
        time.sleep(0.001)  # settle

        # read 4 mux outputs at once
        for mux_adc in adc_channels:
            sensor_values.append(mux_adc.voltage)

    return sensor_values
# --------------------------
# CALIBRATION
# --------------------------

def calibrate_sensors(samples=50, delay=0.01):
    readings = []
    for _ in range(samples):
        readings.append(read_all_sensors())
        time.sleep(delay)
    avg_vals = np.mean(readings, axis=0)

    mins = avg_vals
    maxs = avg_vals + 0.5  # initial guess range
    return mins, maxs
# --------------------------
# NORMALISATION + HEATMAP
# --------------------------

def update_heatmap(vals, mins, maxs):
    # Expand max dynamically
    for i, v in enumerate(vals):
        if v > maxs[i]:
            maxs[i] = v

    norm_vals = (np.array(vals) - mins) / (maxs - mins)
    norm_vals = np.clip(norm_vals, 0, 1)
    grid = norm_vals.reshape((NUM_ROWS, NUM_COLS))
    return grid, maxs
# --------------------------
# MAIN
# --------------------------

def main():
    mins, maxs = calibrate_sensors()
    print("Calibration complete.")

    plt.ion()
    fig, ax = plt.subplots()
    cmap = plt.cm.inferno
    norm = mcolors.Normalize(vmin=0, vmax=1)
    im = ax.imshow(np.zeros((NUM_ROWS, NUM_COLS)), cmap=cmap, norm=norm)

    while True:
        vals = read_all_sensors()
        grid, maxs = update_heatmap(vals, mins, maxs)

        im.set_data(grid)
        plt.draw()
        plt.pause(0.05)

if __name__ == "__main__":
    try:
        main()
    finally:
        GPIO.cleanup()











 """"   
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

################################
# Graveyard has no sensors now just 1 for users to place 
################################
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


def enable_mux(index):
    # Enable one MUX at a time (active LOW)
    for i, pin in enumerate(MUX_ENABLE_PINS):
        GPIO.output(pin, GPIO.LOW if i == index else GPIO.HIGH)

def read_all_sensors():     #Hall effect grid class, self.values in those values there is a dictionary of all sensors, 2 dictionaies in it
    # 1 for all sensors and the other the continuos ones. 
    # We want a method that populates the dictionary when called.
    # using this we can use the weighted graph to figure out where pieces are on the board. 
    # needs to figure out when state changes to trigger this function as itll have to run continuosly. 
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


"""