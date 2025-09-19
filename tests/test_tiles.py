#!/usr/bin/env python3
import time, sys, os
import smbus2
from smbus2 import i2c_msg
import RPi.GPIO as GPIO
#RUN BOARD AT #3.3V
# ========= CONFIG =========
BUS_ID     = 1
ADDR       = 0x10       # TLA2528 I2C address
AVDD       = 5.0 #Leave this       
MUX_PINS   = [16,17,18,19]  # BCM: S0..S3
MUX_SETTLE = 0.002
ADC_CHS    = [0,1,2,3,4]    # AIN0..AIN4 (5 mux boards)

# ========= Thresholds =========
BASE_V  = 2.5   # mid-level in volts (Change to 2.5 if running at 5V, 0r 1.65 at 3.3v)
THRESH  = 0.20
LOWER, UPPER = BASE_V - THRESH, BASE_V + THRESH

def is_magnet(v: float) -> int: #Check if the magnet is there
    return 1 if (v < LOWER or v > UPPER) else 0

# ========= ADC (TLA2528, MANUAL MODE) =========
READ_TRIES = 3

def general_call_reset(bus):
    try:
        bus.write_i2c_block_data(0x00, 0x06, [])
        time.sleep(0.01)
    except Exception:
        pass

def adc_init(bus):
    REG_DATA_CFG      = 0x02
    REG_OSR_CFG       = 0x03
    REG_PIN_CFG       = 0x05
    REG_SEQUENCE_CFG  = 0x10
    bus.write_byte_data(ADDR, REG_SEQUENCE_CFG, 0x00)  # manual mode
    bus.write_byte_data(ADDR, REG_PIN_CFG,      0x00)  # all analog
    bus.write_byte_data(ADDR, REG_OSR_CFG,      0x00)  # no OSR
    bus.write_byte_data(ADDR, REG_DATA_CFG,     0x00)  # default frame
    time.sleep(0.002)

def adc_select_channel(bus, ch: int):
    wr = i2c_msg.write(ADDR, [0x08, 0x11, ch & 0x0F])
    bus.i2c_rdwr(wr)

def adc_read_code12(bus):
    for _ in range(READ_TRIES):
        try:
            rd = i2c_msg.read(ADDR, 3)
            bus.i2c_rdwr(rd)
            b = list(rd)
            return ((b[0] << 8) | b[1]) >> 4
        except Exception:
            time.sleep(0.0005)
    rd = i2c_msg.read(ADDR, 2)
    bus.i2c_rdwr(rd)
    b = list(rd)
    return ((b[0] << 8) | b[1]) >> 4

def adc_read_voltage(bus, ch: int) -> float:
    adc_select_channel(bus, ch)
    code12 = adc_read_code12(bus)
    return (code12 & 0x0FFF) * AVDD / 4095.0

# ========= 4067 (GPIO) =========
def mux_init():
    GPIO.setmode(GPIO.BCM)
    for p in MUX_PINS:
        GPIO.setup(p, GPIO.OUT, initial=GPIO.LOW)

def mux_set(ch: int):
    for i, pin in enumerate(MUX_PINS):
        GPIO.output(pin, (ch >> i) & 1)

def mux_cleanup():
    GPIO.cleanup()

# ========= Terminal helpers =========
def clear_screen():
    sys.stdout.write("\033[H\033[J")  # cursor home, clear screen
    sys.stdout.flush()

# ========= MAIN =========
def main():
    mux_init()
    bus = smbus2.SMBus(BUS_ID)
    try:
        general_call_reset(bus)
        adc_init(bus)

        while True:
            # --- Build bitmap (10×8 grid = 80 sensors) ---
            bitmap = []
            for ain in ADC_CHS:          # 5 rows of 16 each
                row = []
                for m in range(16):
                    mux_set(m)
                    time.sleep(MUX_SETTLE)
                    v = adc_read_voltage(bus, ain)
                    row.append(is_magnet(v))
                bitmap.append(row)

            # --- Draw on terminal ---
            clear_screen()
            print("Live 10×8 Sensor Map (AIN0–AIN4 × mux 0–15):\n")
            for ain_idx, row in enumerate(bitmap):
                top = row[:8]
                bot = row[8:][::-1]  # reverse second half for orientation
                print("RowTop (AIN%d): " % ain_idx + " ".join(str(x) for x in top))
                print("RowBot (AIN%d): " % ain_idx + " ".join(str(x) for x in bot))
            print("\n[Press Ctrl+C to stop]")

            time.sleep(0.01)  # refresh rate

    except KeyboardInterrupt:
        pass
    finally:
        bus.close()
        mux_cleanup()

if __name__ == "__main__":
    main()
