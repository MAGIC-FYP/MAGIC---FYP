import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# Setup I2C and two ADCs with different I2C addresses
i2c = busio.I2C(board.SCL, board.SDA)
ads1 = ADS.ADS1115(i2c, address=0x48)  # Default address
ads2 = ADS.ADS1115(i2c, address=0x49)  # Second ADS1115

ads1.gain = 1
ads2.gain = 1

# Map sensors to logical squares (adjusted for 8)
square_map = [
    ["A1", "B1", "C1", "D1"],
    ["A2", "B2", "C2", "D2"]
]

# Create analog channels: 4 from each ADS
channels = [AnalogIn(ads1, getattr(ADS, f"P{i}")) for i in range(4)] + \
           [AnalogIn(ads2, getattr(ADS, f"P{i}")) for i in range(4)]  # 8 sensors total

# Read voltages for calibration
def read_all_sensors():
    return [ch.voltage for ch in channels]

# 1. Calibrate minimum (no magnet on any)
print("Calibrating MIN voltage. No magnets should be placed...")
time.sleep(3)
min_voltages = read_all_sensors()
min_avg = sum(min_voltages) / len(min_voltages)
print("Min average voltage:", min_avg)

# 2. Calibrate maximum (place magnet only on sensor 0)
input("Place magnet on sensor 0, then press Enter...")
max_voltages = read_all_sensors()
max_val = max_voltages[0]
print("Max voltage on sensor 0:", max_val)

# 3. Set thresholds
max_threshold = max_val - 0.05
min_threshold = min_avg + 0.05
print("Thresholds — max:", max_threshold, "min:", min_threshold)

#******************************************************************#
# 4. Run test loop (simulate 1 pickup + place)
print("\nRunning sensor change detection...\n")
previous_states = read_all_sensors()

try:
    while True:
        current_states = read_all_sensors()
        for i, (prev, curr) in enumerate(zip(previous_states, current_states)):
            if prev > max_threshold and curr < max_threshold:
                row, col = divmod(i, 4)
                print(f"Piece PICKED UP from {square_map[row][col]}")
            elif prev < min_threshold and curr > min_threshold:
                row, col = divmod(i, 4)
                print(f"Piece PLACED on {square_map[row][col]}")
        previous_states = current_states
        time.sleep(0.5)

except KeyboardInterrupt:
    print("Stopped.")
