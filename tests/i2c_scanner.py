#!/usr/bin/env python3
import smbus2
from time import sleep

def main():
    bus = smbus2.SMBus(1)
    found = []
    for addr in range(0x03, 0x78):
        try:
            bus.write_quick(addr)  # will ACK if a device is present
            found.append(addr)
        except Exception:
            pass
    bus.close()
    if not found:
        print("No I2C devices responded on bus 1. Check power/SDA/SCL, enable I2C (raspi-config).")
    else:
        print("I2C devices found:", " ".join(f"0x{a:02X}" for a in found))

if __name__ == "__main__":
    main()
