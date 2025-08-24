import time
import smbus2
import RPi.GPIO as GPIO

# ---------------------
# TLA2528 ADC Driver
# ---------------------
class TLA2528:
    # Register map (partial, check datasheet for full)
    REG_RESULT   = 0x00
    REG_CONFIG   = 0x01
    REG_INPUTMUX = 0x02
    REG_CONFIG2  = 0x03

    def __init__(self, bus_id=1, address=0x18, vref=5.0):
        self.bus = smbus2.SMBus(bus_id)
        self.addr = address
        self.vref = vref  # Reference voltage (adjust for your circuit!)

        # Default config: 16-bit, OSR=128 (high precision)
        # CONFIG2 bits: [7:6]=OSR, [5:4]=Resolution, others reserved
        # Example: 0b01000011 -> OSR=128, 16-bit mode
        self.config2 = 0x43
        self.bus.write_byte_data(self.addr, self.REG_CONFIG2, self.config2)

    def read_raw(self, channel: int) -> int:
        """
        Perform a single-shot conversion on the given channel (0–7).
        Returns raw 16-bit ADC value.
        """
        if not (0 <= channel <= 7):
            raise ValueError("Channel must be 0–7")

        # Select channel
        self.bus.write_byte_data(self.addr, self.REG_INPUTMUX, channel & 0x07)

        # Start single-shot conversion
        config = 0x80  # Bit 7 = START
        self.bus.write_byte_data(self.addr, self.REG_CONFIG, config)

        # Wait for conversion (~2ms worst case at 16-bit OSR=128)
        time.sleep(0.002)

        # Read result (2 bytes)
        data = self.bus.read_i2c_block_data(self.addr, self.REG_RESULT, 2)
        raw = (data[0] << 8) | data[1]

        return raw

    def read_voltage(self, channel: int) -> float:
        """Return voltage value from ADC channel (scaled by Vref)."""
        raw = self.read_raw(channel)
        voltage = (raw / 65535.0) * self.vref
        return voltage

    def close(self):
        self.bus.close()


# ---------------------
# Multiplexer Setup
# ---------------------
MUX_PINS = [17, 27, 22, 23]  # BCM GPIO numbers for S0–S3
ADC_CHANNEL = 0              # TLA2528 input tied to mux output

GPIO.setmode(GPIO.BCM)
for pin in MUX_PINS:
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

def set_mux_channel(channel: int):
    """Select one of the 16 mux channels (0–15)."""
    for i, pin in enumerate(MUX_PINS):
        GPIO.output(pin, (channel >> i) & 1)


# ---------------------
# MAIN PROGRAM
# ---------------------
def main():
    adc = TLA2528(bus_id=1, address=0x18, vref=5.0)  # adjust vref!
    try:
        while True:
            readings = []
            for ch in range(16):
                set_mux_channel(ch)
                time.sleep(0.001)  # allow mux to settle
                value = adc.read_voltage(ADC_CHANNEL)
                readings.append(round(value, 3))  # round to mV precision
            print("Sensor voltages (V):", readings)
            time.sleep(1)

    except KeyboardInterrupt:
        pass
    finally:
        adc.close()
        GPIO.cleanup()


if __name__ == "__main__":
    main()
