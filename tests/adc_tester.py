#!/usr/bin/env python3
import time
import smbus2
from smbus2 import i2c_msg

# ---------- Config ----------
BUS_ID    = 1
ADDR      = 0x10          # your i2c address
AVDD      = 5.0           # ADC reference (AVDD)
READ_TRIES = 3            # small retry on read

# --- TLA2528 registers used for setup ---
REG_DATA_CFG      = 0x02
REG_OSR_CFG       = 0x03
REG_PIN_CFG       = 0x05
REG_SEQUENCE_CFG  = 0x10
REG_CHANNEL_SEL   = 0x11   # for clarity; we’ll also use the 0x08 opcode

def general_call_reset(bus):
    try:
        # General Call address 0x00, “Reset” command 0x06
        bus.write_i2c_block_data(0x00, 0x06, [])
        time.sleep(0.01)
    except Exception:
        pass

def init_adc(bus):
    # Known-good baseline; MANUAL mode (sequencer stopped)
    bus.write_byte_data(ADDR, REG_SEQUENCE_CFG, 0x00)  # stop sequencer/manual
    bus.write_byte_data(ADDR, REG_PIN_CFG,      0x00)  # all pins analog inputs
    bus.write_byte_data(ADDR, REG_OSR_CFG,      0x00)  # no oversampling (fast)
    bus.write_byte_data(ADDR, REG_DATA_CFG,     0x00)  # default data framing
    time.sleep(0.002)

def select_channel_opcode(bus, ch: int):
    """
    Use the TI command frame you pasted:
      [ OPCODE=0x08, REGISTER=0x11 (CHANNEL_SEL), VALUE=<ch> ]
    We send it as a raw I2C write (no SMBus register byte).
    """
    if not (0 <= ch <= 7):
        raise ValueError("channel must be 0..7")
    wr = i2c_msg.write(ADDR, [0x08, 0x11, ch & 0x0F])
    bus.i2c_rdwr(wr)

def read_frame(bus):
    """
    Try to read 3 bytes (most boards return 3 in manual mode).
    Fall back to 2 bytes if 3 fails. Returns (code12, nbytes).
    """
    # Try 3-byte read
    for _ in range(READ_TRIES):
        try:
            rd = i2c_msg.read(ADDR, 3)
            bus.i2c_rdwr(rd)
            b = list(rd)
            # 12-bit left-justified across first two bytes
            code12 = ((b[0] << 8) | b[1]) >> 4
            return code12 & 0x0FFF, 3
        except Exception:
            time.sleep(0.0005)
    # Fallback to 2-byte read
    rd = i2c_msg.read(ADDR, 2)
    bus.i2c_rdwr(rd)
    b = list(rd)
    code12 = ((b[0] << 8) | b[1]) >> 4
    return code12 & 0x0FFF, 2

def read_voltage(bus, ch: int) -> float:
    select_channel_opcode(bus, ch)
    # The device clock-stretches until conversion ready; just read the frame
    code12, _ = read_frame(bus)
    return (code12 / 4095.0) * AVDD

def main():
    bus = smbus2.SMBus(BUS_ID)
    try:
        general_call_reset(bus)
        init_adc(bus)

        chans = [0, 1, 2, 3, 4]  # AIN0..AIN4
        while True:
            volts = []
            for ch in chans:
                v = read_voltage(bus, ch)
                volts.append(v)
            print(" | ".join(f"AIN{ch}:{volts[i]:0.3f}V" for i, ch in enumerate(chans)))
            time.sleep(1.0)

    except KeyboardInterrupt:
        pass
    finally:
        bus.close()

if __name__ == "__main__":
    main()
