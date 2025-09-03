import time
import board
import busio
import numpy as np
import RPi.GPIO as GPIO  # Assuming Raspberry Pi for GPIO control
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from detector_config import MUXConfig


class HallSensors:
    """
    INITIALISATION:
    - Create a PieceDetector object to handle the detection of pieces in the game, via hall effect sensors. 
    """

    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        self.main_board_states = np.zeros((8,8))
        self.white_graveyard_state = 0
        self.black_graveyard_state = 0

        self.upper_thresh = None # Upper threshold for sensor activation
        self.lower_thresh = None  # Lower threshold for sensor activation
  
        self._init_adc()  # Initialise ADC for sensor readings
        self._init_mux()  # Initialise MUX for channel selection

    def _init_adc(self):
        """
        Initialise the ADC (Analog to Digital Converter) for reading sensor values.
        This method should be implemented in subclasses.
        """
        i2c = busio.I2C(board.SCL, board.SDA)
        ads = ADS.ADS1115(i2c)
        self.adc_channel = AnalogIn(ads, ADS.P0)

    def _init_mux(self):
        """
        Initialise the multiplexer for selecting sensor channels.
        This method should be implemented in subclasses.
        """
        GPIO.setup(MUXConfig.MUX_SELECT_CHANNELS, GPIO.OUT)
        GPIO.setup(MUXConfig.MUX_ENABLE_CHANNELS, GPIO.OUT)

    # ============================================================================
    # MULTIPLEXOR HELPER METHODS
    # ============================================================================
    
    '''
    The multiplexor logic is as follows:
    - The 16 MUX channels are selected using GPIO pins S0, S1, S2, and S3. (4 bit binary representation)
    - There are 6 MUXes, each with 16 channels, controlled by 6 enable pins (MUX1E to MUX6E).
    - Each MUX can be enabled or disabled using its respective enable pin.
    - The first four MUXes (MUX1E to MUX4E) are used for discrete sensors, while the last two (MUX5E and MUX6E) are used for continuous sensors.
      MUX1E (index 0) channels 0-7 is used for row 1 and channels 8-15 is used for row 2. And so forth MUX5E (index 4) channels 0 and 1 are used
      for the white player graveyard and black player graveyard.
    '''

    def _select_mux_channel(self, channel):
        """
        Select a specific MUX channel.
        :param channel: The channel to select (0-15).
        """
        if 0 <= channel < len(MUXConfig.MUX_SELECT_CHANNELS):
            GPIO.output(MUXConfig.MUX_SELECT_CHANNELS, [int(x) for x in format(channel, '04b')])
        else:
            raise ValueError("Channel out of range. Must be between 0 and 15.")

    def _enable_mux(self, index):
        """
        Enable a specific MUX channel.
        :param index: The index of the MUX channel to enable (0-5).
        """
        if 0 <= index < len(MUXConfig.MUX_ENABLE_CHANNELS):
            GPIO.output(MUXConfig.MUX_ENABLE_CHANNELS[index], GPIO.HIGH)
        else:
            raise ValueError("MUX index out of range. Must be between 0 and 5.")
        
    def _disable_mux(self, index):
        """
        Disable a specific MUX channel.
        :param index: The index of the MUX channel to disable (0-5).
        """
        if 0 <= index < len(MUXConfig.MUX_ENABLE_CHANNELS):
            GPIO.output(MUXConfig.MUX_ENABLE_CHANNELS[index], GPIO.LOW)
        else:
            raise ValueError("MUX index out of range. Must be between 0 and 5.")
        
    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    def _read_sensor_values(self):
        """
        Iterate over all sensors and read their values. 

        """
        board_states = np.zeros((8,8))
        white_graveyard_state = 0
        black_graveyard_state = 0
        continuous_states = []

        row_index = 0

        for mux_index in range(len(MUXConfig.MUX_ENABLE_CHANNELS)):
            self._enable_mux(mux_index)
            for channel in range(16):
                self._select_mux_channel(channel)
                time.sleep(0.001)
                sensor_value = self.adc_channel.value

                if channel < 8 and row_index < 7:
                    board_states[row_index, channel] = sensor_value
                if channel >= 8 and row_index < 7:
                    board_states[row_index+1, channel - 8] = sensor_value
            
                if mux_index == 4:
                    if channel == 0:
                        white_graveyard_state = sensor_value
                    elif channel == 1:
                        black_graveyard_state = sensor_value
                    else:
                        continuous_states.append(sensor_value)

                if mux_index >4:
                    continuous_states.append(sensor_value)
                
            self._disable_mux(mux_index)
            row_index += 2
        
        return board_states, white_graveyard_state, black_graveyard_state, continuous_states
            


    