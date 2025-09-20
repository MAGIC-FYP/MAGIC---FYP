#!/usr/bin/env python3
import time
import smbus2
from smbus2 import i2c_msg
import RPi.GPIO as GPIO

# ---------- USER CONFIG ----------
BUS_ID       = 1
ADC_ADDR     = 0x10   # you confirmed this
AVDD_VOLTS   = 5.0
MUX_PINS_BCM = [16,17,18,19]
MUX_SETTLE_S = 0.002
SAFE_TIMEOUT = 0.05   # seconds

# ---------- ADC REG ----------
REG_DATA_CFG      = 0x02
REG_OSR_CFG       = 0x03
REG_PIN_CFG       = 0x05
REG_SEQUENCE_CFG  = 0x10
REG_CHANNEL_SEL   = 0x11
REG_AUTO_SEQ_SEL  = 0x12

def i2c_read(bus, addr, n):
    rd = i2c_msg.read(addr, n)
    bus.i2c_rdwr(rd)
    return list(rd)

def general_call_reset(bus):
    try:
        bus.write_i2c_block_data(0x00, 0x06, [])
        time.sleep(0.01)
    except Exception:
        pass

def write_reg(bus, reg, val):
    bus.write_byte_data(ADC_ADDR, reg, val)

def start_sequencer(bus, mask_0_to_4=True):
    # all analog inputs, no OSR, default data
    write_reg(bus, REG_PIN_CFG, 0x00)
    write_reg(bus, REG_OSR_CFG, 0x00)
    write_reg(bus, REG_DATA_CFG, 0x00)
    write_reg(bus, REG_SEQUENCE_CFG, 0x00)  # stop
    if mask_0_to_4:
        write_reg(bus, REG_AUTO_SEQ_SEL, 0b0001_1111)
    else:
        write_reg(bus, REG_AUTO_SEQ_SEL, 0x00)
    write_reg(bus, REG_SEQUENCE_CFG, 0x11)  # SEQ_MODE=01, START=1
    time.sleep(0.002)

def decode_frame_4(b):
    """Return (chid_guess, code12, volts) for 4-byte frame."""
    status, msb, lsb, extra = b
    code12 = ((msb << 8) | lsb) >> 4
    chid_low  = status & 0x0F
    chid_high = (status >> 4) & 0x0F
    volts  = (code12 / 4095.0) * AVDD_VOLTS
    return chid_low, chid_high, code12, volts

def read_next_safe(bus, timeout_s=SAFE_TIMEOUT):
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        try:
            f = i2c_read(bus, ADC_ADDR, 4)
            return f
        except Exception:
            time.sleep(0.001)
    return None

def manual_read_once(bus, ch):
    """Manual mode: pick channel and read 3 or 2 bytes robustly."""
    # stop sequencer
    write_reg(bus, REG_SEQUENCE_CFG, 0x00)
    # select channel
    write_reg(bus, REG_CHANNEL_SEL, ch & 0x0F)
    # small wait, then read 3 bytes; if it fails, read 2 bytes
    time.sleep(0.001)
    try:
        b = i2c_read(bus, ADC_ADDR, 3)
        msb, mid, lsb = b[0], b[1], b[2]
        code12 = ((msb << 8) | mid) >> 4
    except Exception:
        b = i2c_read(bus, ADC_ADDR, 2)
        msb, lsb = b[0], b[1]
        code12 = ((msb << 8) | lsb) >> 4
    volts = (code12 / 4095.0) * AVDD_VOLTS
    return volts

def mux_init():
    GPIO.setmode(GPIO.BCM)
    for p in MUX_PINS_BCM:
        GPIO.setup(p, GPIO.OUT, initial=GPIO.LOW)

def set_mux_channel(ch):
    for i, pin in enumerate(MUX_PINS_BCM):
        GPIO.output(pin, (ch >> i) & 1)

def mux_cleanup():
    GPIO.cleanup()

def main():
    mux_init()
    bus = smbus2.SMBus(BUS_ID)
    try:
        print(f"[INFO] Bus {BUS_ID}, ADC @ 0x{ADC_ADDR:02X}")
        general_call_reset(bus)

        # A) SMOKE: dump a few raw frames (never hang)
        print("[SMOKE] Reading 8 raw frames:")
        for i in range(8):
            f = read_next_safe(bus, timeout_s=SAFE_TIMEOUT)
            if f is None:
                print(f"  {i:02d}: (timeout)")
            else:
                print(f"  {i:02d}: " + " ".join(f"{x:02X}" for x in f))

        # B) Sequencer start + CHID sanity check
        start_sequencer(bus, mask_0_to_4=True)
        print("[SEQ] Verifying CHIDs… (expect 0..4 cycling)")
        seen = []
        for _ in range(40):
            f = read_next_safe(bus, timeout_s=SAFE_TIMEOUT)
            if f is None:
                print("  frame: (timeout)")
                continue
            cl, ch, code12, volts = decode_frame_4(f)
            seen.append(cl)
            print(f"  frame: {' '.join(f'{x:02X}' for x in f)}  -> CHID? low={cl} high={ch}  {volts:0.3f}V")
        uniq = sorted(set(seen))
        print(f"[SEQ] Low-nibble CHIDs seen: {uniq}")

        seq_ok = set(uniq).issubset({0,1,2,3,4}) and len(uniq) >= 3
        if not seq_ok:
            print("[WARN] Sequencer CHIDs don’t look right. We’ll still try a MUX sweep and also do a manual-mode sweep as a cross-check.")

        # C) MUX sweep (sequencer vector AIN0..AIN4 with timeouts → no hang)
        print("\n[SWEEP: sequencer] MUX 0..15 (AIN0..AIN4):")
        for chmux in range(16):
            set_mux_channel(chmux)
            time.sleep(MUX_SETTLE_S)
            got = {i: None for i in range(5)}
            t0 = time.time()
            while None in got.values() and time.time() - t0 < 0.15:
                f = read_next_safe(bus, timeout_s=SAFE_TIMEOUT)
                if f is None:
                    continue
                cl, ch, code12, volts = decode_frame_4(f)
                if 0 <= cl <= 4 and got[cl] is None:
                    got[cl] = volts
            line = f" MUX {chmux:02d} | " + " | ".join(
                f"AIN{i}:{(got[i] if got[i] is not None else float('nan')):0.3f}V" for i in range(5)
            )
            print(line)

        # D) Cross-check: manual-mode reads on AIN0..AIN4 (no sequencer involved)
        print("\n[SWEEP: manual mode] MUX 0..15 (AIN0..AIN4):")
        for chmux in range(16):
            set_mux_channel(chmux)
            time.sleep(MUX_SETTLE_S)
            vals = []
            for ain in range(5):
                v = manual_read_once(bus, ain)
                vals.append(v)
            line = f" MUX {chmux:02d} | " + " | ".join(f"AIN{i}:{vals[i]:0.3f}V" for i in range(5))
            print(line)

        print("\n[HINTS]")
        print("• If sequencer CHIDs above didn’t stay in 0..4, rely on the MANUAL MODE block for now.")
        print("• If AIN1..AIN4 read ~2.5V and drift, they’re floating → add ~100kΩ to GND on each AIN.")
        print("• One 4067 COM pin should feed exactly one ADC AIN. Unused AINs must be biased (pull-down).")

    except KeyboardInterrupt:
        pass
    finally:
        bus.close()
        mux_cleanup()

if __name__ == "__main__":
    main()
