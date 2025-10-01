#!/usr/bin/env python3
import time, sys, os
import smbus2
from smbus2 import i2c_msg
import RPi.GPIO as GPIO
import numpy as np

#RUN BOARD AT #3.3V

class TileSensor:
    """
    A class to interface with the tile sensor array, including ADC (TLA2528)
    and MUX (4067) for reading magnet presence.
    """

    # ========= CONFIG (Class-level defaults, can be overridden in __init__) =========
    BUS_ID     = 1
    ADDR       = 0x10       # TLA2528 I2C address
    AVDD       = 5.0        # Analog supply voltage for ADC
    MUX_PINS   = [16,17,18,19]  # BCM GPIO pins for MUX S0..S3
    MUX_SETTLE = 0.002      # Time in seconds for MUX to settle after channel change
    ADC_CHS    = [0,1,2,3,4]    # AIN0..AIN4 (5 mux boards)

    # ========= Thresholds (Class-level defaults) =========
    BASE_V     = 2.5        # Mid-level voltage for magnet detection
    THRESH     = 0.20       # Threshold deviation from BASE_V to detect magnet
    READ_TRIES = 3          # Number of attempts to read ADC data

    # ADC Register definitions (internal to ADC operations)
    _REG_DATA_CFG      = 0x02
    _REG_OSR_CFG       = 0x03
    _REG_PIN_CFG       = 0x05
    _REG_SEQUENCE_CFG  = 0x10

    def __init__(self, bus_id: int = None, addr: int = None, avdd: float = None,
                 mux_pins: list[int] = None, mux_settle: float = None,
                 adc_chs: list[int] = None, base_v: float = None,
                 thresh: float = None):
        """
        Initializes the TileSensor.
        Configures GPIO for MUX and initializes the I2C bus and ADC.
        """
        # Override class defaults with instance-specific values if provided
        self.bus_id = bus_id if bus_id is not None else self.BUS_ID
        self.addr = addr if addr is not None else self.ADDR
        self.avdd = avdd if avdd is not None else self.AVDD
        self.mux_pins = mux_pins if mux_pins is not None else self.MUX_PINS
        self.mux_settle = mux_settle if mux_settle is not None else self.MUX_SETTLE
        self.adc_chs = adc_chs if adc_chs is not None else self.ADC_CHS
        self.base_v = base_v if base_v is not None else self.BASE_V
        self.thresh = thresh if thresh is not None else self.THRESH

        # Calculate magnet detection thresholds
        self.lower_threshold = self.base_v - self.thresh
        self.upper_threshold = self.base_v + self.thresh

        self.bus = None
        self._init_hardware()

    def _init_hardware(self):
        """Initializes RPi.GPIO for MUX and the I2C bus for ADC with retry logic."""
        # MUX GPIO setup
        GPIO.setmode(GPIO.BCM)
        for p in self.mux_pins:
            GPIO.setup(p, GPIO.OUT, initial=GPIO.LOW)

        # I2C bus and ADC initialization with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.bus = smbus2.SMBus(self.bus_id)
                self._general_call_reset()
                self._adc_init()
                print("ADC initialized successfully")
                return  # Success
            except Exception as e:
                print(f"ADC init attempt {attempt + 1} failed: {e}", file=sys.stderr)
                if self.bus:
                    try:
                        self.bus.close()
                    except:
                        pass
                if attempt < max_retries - 1:
                    time.sleep(0.5)  # Wait before retry
                else:
                    print("WARNING: Could not initialize ADC hardware after retries", file=sys.stderr)
                    # Graceful degradation - set bus to None but don't crash
                    self.bus = None

    def _is_magnet(self, v: float) -> int:
        """
        Checks if the given voltage indicates the presence of a magnet.
        Returns 1 if magnet is detected, 0 otherwise.
        """
        return 1 if (v < self.lower_threshold or v > self.upper_threshold) else 0

    # ========= ADC (TLA2528, MANUAL MODE) Methods =========
    def _general_call_reset(self):
        """Performs an I2C general call reset."""
        try:
            self.bus.write_i2c_block_data(0x00, 0x06, [])
            time.sleep(0.01)
        except Exception:
            # Original code suppresses this error, so we do too.
            pass

    def _adc_init(self):
        """Initializes the TLA2528 ADC for manual mode operation."""
        self.bus.write_byte_data(self.addr, self._REG_SEQUENCE_CFG, 0x00)  # manual mode
        self.bus.write_byte_data(self.addr, self._REG_PIN_CFG,      0x00)  # all analog
        self.bus.write_byte_data(self.addr, self._REG_OSR_CFG,      0x00)  # no OSR
        self.bus.write_byte_data(self.addr, self._REG_DATA_CFG,     0x00)  # default frame
        time.sleep(0.002)

    def _adc_select_channel(self, ch: int):
        """Selects the specified analog input channel on the ADC."""
        if self.bus is None:
            raise RuntimeError("I2C bus not initialized")
        wr = i2c_msg.write(self.addr, [0x08, 0x11, ch & 0x0F])
        self.bus.i2c_rdwr(wr)

    def _adc_read_code12(self) -> int:
        """
        Reads a 12-bit ADC code from the TLA2528.
        Attempts multiple reads if errors occur.
        """
        if self.bus is None:
            raise RuntimeError("I2C bus not initialized")
        for _ in range(self.READ_TRIES):
            try:
                rd = i2c_msg.read(self.addr, 3) # Attempt 3-byte read
                self.bus.i2c_rdwr(rd)
                b = list(rd)
                return ((b[0] << 8) | b[1]) >> 4 # Extract 12-bit code
            except Exception:
                time.sleep(0.0005)
        # Fallback to 2-byte read if 3-byte fails repeatedly (as in original code)
        rd = i2c_msg.read(self.addr, 2)
        self.bus.i2c_rdwr(rd)
        b = list(rd)
        return ((b[0] << 8) | b[1]) >> 4

    def _adc_read_voltage(self, ch: int) -> float:
        """
        Reads the voltage from the specified ADC channel.
        Selects the channel, reads the 12-bit code, and converts to voltage.
        """
        self._adc_select_channel(ch)
        code12 = self._adc_read_code12()
        return (code12 & 0x0FFF) * self.avdd / 4095.0

    # ========= 4067 (GPIO) MUX Methods =========
    def _mux_set(self, ch: int):
        """Sets the 4067 MUX to the specified channel."""
        for i, pin in enumerate(self.mux_pins):
            GPIO.output(pin, (ch >> i) & 1)

    # ========= Terminal helpers (Static methods as they don't need instance state) =========
    @staticmethod
    def _clear_screen():
        """Clears the terminal screen."""
        sys.stdout.write("\033[H\033[J")  # cursor home, clear screen
        sys.stdout.flush()

    # ========= Public Interface Methods =========
    def get_sensor_bitmap(self) -> list[list[int]]:
        """
        Reads the current state of all sensors (5 AIN channels x 16 MUX channels)
        and returns a 2D list (bitmap) indicating magnet presence.
        Final output is 10x8, flipped along the anti-diagonal (top-right to bottom-left).
        """
        if self.bus is None:
            print("WARNING: I2C bus not initialized, returning empty bitmap", file=sys.stderr)
            return np.zeros((10, 8), dtype=int).tolist()
        
        try:
            n_ain = len(self.adc_chs)
            raw_sensor_data = np.zeros((n_ain, 16), dtype=int)

            # Collect all ADC readings (5 x 16)
            for ain_idx, ain_channel in enumerate(self.adc_chs):
                for mux_channel in range(16):
                    self._mux_set(mux_channel)
                    time.sleep(self.mux_settle)
                    v = self._adc_read_voltage(ain_channel)
                    raw_sensor_data[ain_idx, mux_channel] = self._is_magnet(v)

            # Build 10x8 bitmap
            final_bitmap = np.zeros((n_ain * 2, 8), dtype=int)
            final_bitmap[0::2, :] = raw_sensor_data[:, :8]               # first 8 samples → top row
            final_bitmap[1::2, :] = raw_sensor_data[:, 8:][:, ::-1]      # last 8 samples → reversed bottom row

            # Flip along the anti-diagonal (↘)
            flipped = np.flipud(np.fliplr(final_bitmap.T))

            final_bitmap = flipped[:, ::-1]

            return final_bitmap.tolist()
        except Exception as e:
            print(f"Error reading sensor bitmap: {e}", file=sys.stderr)
            return np.zeros((10, 8), dtype=int).tolist()


    def display_bitmap(self, bitmap):
        """
        Prints the sensor bitmap to the terminal in a human-readable format
        and returns a new array containing only the 8-element data rows
        (top and reversed bottom halves) that were displayed.
        """
        for i in bitmap:
            print(i)
        print()
        return True

    def run_live_display(self, refresh_rate: float = 0.01):
        """
        Runs a continuous loop to read sensor data and display it on the terminal.
        Exits gracefully on KeyboardInterrupt.
        """
        try:
            while True:
                bitmap = self.get_sensor_bitmap()
                for i in bitmap:
                    print(i)
                print()
                time.sleep(refresh_rate)
        except KeyboardInterrupt:
            print("\nExiting live display.")
            pass # Allow graceful exit on Ctrl+C

    def close(self):
        """
        Cleans up RPi.GPIO resources and closes the I2C bus connection.
        Should be called when the sensor is no longer needed.
        """
        if self.bus:
            self.bus.close()
            self.bus = None
        GPIO.cleanup()

    def __enter__(self):
        """Context manager entry point."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point, ensures cleanup."""
        self.close()

# ========= MAIN (Example Usage) =========
if __name__ == "__main__":
    # To use the TileSensor class, instantiate it and call its methods.
    # The 'with' statement ensures that resources are properly cleaned up
    # even if errors occur or the program is interrupted.
    try:
        with TileSensor() as sensor:
            sensor.run_live_display()
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
