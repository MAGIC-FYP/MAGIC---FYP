import smbus
import time

import sys # Import sys to exit gracefully if I2C fails


#TODO:
# - Add higher level function that handles conversion of menu into LCD
# - Add a function to display a message on the LCD for a certain amount of time

class LCD:
    def __init__(self, pi_rev = 2, i2c_addr = 0x27, backlight = True, flipped = False): # Added 'flipped' parameter

        # device constants
        self.I2C_ADDR  = i2c_addr
        self.LCD_WIDTH = 16   # Max. characters per line

        self.LCD_CHR = 1 # Mode - Sending data
        self.LCD_CMD = 0 # Mode - Sending command

        self.LCD_LINE_1 = 0x80 # LCD RAM addr for line one
        self.LCD_LINE_2 = 0xC0 # LCD RAM addr for line two

        if backlight:
            # on
            self.LCD_BACKLIGHT  = 0x08
        else:
            # off
            self.LCD_BACKLIGHT = 0x00

        self.ENABLE = 0b00000100 # Enable bit

        # Timing constants
        self.E_PULSE = 0.0005
        self.E_DELAY = 0.0005

        self.flipped = flipped # Store the flipped state

        try:
            # Open I2C interface
            if pi_rev == 2:
                # Rev 2 Pi uses 1
                self.bus = smbus.SMBus(2)
                self.bus_id = 1
            elif pi_rev == 1:
                # Rev 1 Pi uses 0
                self.bus = smbus.SMBus(0)
                self.bus_id = 0
            else:
                raise ValueError('pi_rev param must be 1 or 2')

            # Initialise display
            self.lcd_byte(0x33, self.LCD_CMD) # 110011 Initialise
            self.lcd_byte(0x32, self.LCD_CMD) # 110010 Initialise
            self.lcd_byte(0x06, self.LCD_CMD) # 000110 Cursor move direction
            self.lcd_byte(0x0C, self.LCD_CMD) # 001100 Display On,Cursor Off, Blink Off
            self.lcd_byte(0x28, self.LCD_CMD) # 101000 Data length, number of lines, font size
            self.lcd_byte(0x01, self.LCD_CMD) # 000001 Clear display
            print(f"✓ LCD initialized successfully at I2C address 0x{self.I2C_ADDR:02X} on bus {self.bus_id}")

        except OSError as e:
            print(f"Error: Could not communicate with LCD at I2C address 0x{self.I2C_ADDR:02X} on bus {self.bus_id if hasattr(self, 'bus_id') else 'unknown'}.")
            print("Please check:")
            print("  1. The LCD is correctly wired to the Raspberry Pi's I2C pins.")
            print("  2. The I2C address (0x27 by default) is correct for your LCD module.")
            print("     You can find the correct address using 'i2cdetect -y 1' (or 'i2cdetect -y 0' for older Pis).")
            print("  3. I2C is enabled on your Raspberry Pi (e.g., via 'sudo raspi-config').")
            print(f"Original error: {e}")
            sys.exit(1) # Exit the program as the display is essential

    def lcd_byte(self, bits, mode):
        # Send byte to data pins
        # bits = data
        # mode = 1 for data, 0 for command

        bits_high = mode | (bits & 0xF0) | self.LCD_BACKLIGHT
        bits_low = mode | ((bits<<4) & 0xF0) | self.LCD_BACKLIGHT

        # High bits
        self.bus.write_byte(self.I2C_ADDR, bits_high)
        self.toggle_enable(bits_high)

        # Low bits
        self.bus.write_byte(self.I2C_ADDR, bits_low)
        self.toggle_enable(bits_low)

    def toggle_enable(self, bits):
        time.sleep(self.E_DELAY)
        self.bus.write_byte(self.I2C_ADDR, (bits | self.ENABLE))
        time.sleep(self.E_PULSE)
        self.bus.write_byte(self.I2C_ADDR,(bits & ~self.ENABLE))
        time.sleep(self.E_DELAY)

    def set_flipped(self, flipped_state):
        """Set the display's flipped state.
        If True, logical line 1 will map to physical line 2, and logical line 2 to physical line 1.
        """
        self.flipped = bool(flipped_state)

    def get_flipped(self):
        """Get the current flipped state of the display."""
        return self.flipped

    def message(self, string, line=1, scroll=False, scroll_speed=0.3, duration=None):
        """
        Display message string on LCD line 1 or 2.
        
        Args:
            string (str): The message to display.
            line (int): The logical line number (1 or 2) to display the message on.
            scroll (bool): If True, the message will scroll if it's longer than the display width.
            scroll_speed (float): Delay in seconds between each scroll step.
            duration (float, optional): If provided and positive, the message will disappear
                                        (the line will be cleared) after this many seconds.
                                        If None or 0, the message will remain on the display.
        """
        if line == 1:
            target_lcd_line = self.LCD_LINE_1
        elif line == 2:
            target_lcd_line = self.LCD_LINE_2
        else:
            raise ValueError('line number must be 1 or 2')

        # Determine the actual physical LCD line address, considering the 'flipped' state
        actual_lcd_line_for_display = target_lcd_line
        if self.flipped:
            # If flipped, swap the target line addresses
            if actual_lcd_line_for_display == self.LCD_LINE_1:
                actual_lcd_line_for_display = self.LCD_LINE_2
            elif actual_lcd_line_for_display == self.LCD_LINE_2:
                actual_lcd_line_for_display = self.LCD_LINE_1

        # Store the original string to correctly determine if scrolling is needed
        original_string = string
        # Pad or trim the string to at least LCD_WIDTH for static display
        if len(string) < self.LCD_WIDTH:
            string = string.ljust(self.LCD_WIDTH, " ")

        start_time = time.monotonic() # Record start time for duration tracking

        if scroll and len(original_string) > self.LCD_WIDTH:
            # Add spaces to the end for smooth scrolling off the display
            scroll_text = original_string + " " * self.LCD_WIDTH
            num_scroll_steps = len(scroll_text) - self.LCD_WIDTH + 1

            for i in range(num_scroll_steps):
                # Check if the total display duration has been exceeded
                if duration is not None and duration > 0:
                    elapsed_time = time.monotonic() - start_time
                    if elapsed_time >= duration:
                        break # Stop scrolling if duration is reached

                window = scroll_text[i:i + self.LCD_WIDTH]
                self.lcd_byte(actual_lcd_line_for_display, self.LCD_CMD)
                for char in window:
                    self.lcd_byte(ord(char), self.LCD_CHR)
                
                # Sleep for scroll_speed, but respect the remaining duration if specified
                if duration is not None and duration > 0:
                    remaining_duration = duration - (time.monotonic() - start_time)
                    sleep_for = min(scroll_speed, max(0, remaining_duration))
                    time.sleep(sleep_for)
                else:
                    time.sleep(scroll_speed)
        else:
            # Display as much as fits, padded or trimmed
            display_text = string[:self.LCD_WIDTH].ljust(self.LCD_WIDTH, " ")
            self.lcd_byte(actual_lcd_line_for_display, self.LCD_CMD)
            for char in display_text:
                self.lcd_byte(ord(char), self.LCD_CHR)
            
            # If duration is specified, wait for the remaining time
            if duration is not None and duration > 0:
                elapsed_time = time.monotonic() - start_time
                if elapsed_time < duration:
                    time.sleep(duration - elapsed_time)
        
        # After displaying (scrolling or static), if a positive duration was specified, clear the line
        # if duration is not None and duration > 0:
        #     # Clear the line by writing spaces to it
        #     self.lcd_byte(actual_lcd_line_for_display, self.LCD_CMD)
        #     for _ in range(self.LCD_WIDTH):
        #         self.lcd_byte(ord(' '), self.LCD_CHR)

    def clear(self):
        # clear LCD display
        self.lcd_byte(0x01, self.LCD_CMD)

        
# test_lcd_instance = LCD()

# print("Embedded test: Displaying 'Hello, World!' on line 1")
# test_lcd_instance.message("Hello, World!", line=1)
# time.sleep(2)

# print("Embedded test: Displaying 'Python RPi' on line 2")
# test_lcd_instance.message("Python RPi", line=2)
# time.sleep(2)

# print("Embedded test: Testing scrolling message on line 2")
# long_message = "This is a very long message that should scroll across the 16-character display."
# test_lcd_instance.message(long_message, line=2, scroll=True, scroll_speed=0.3)
# time.sleep(2) # Give it some time to scroll

# print("Embedded test: Clearing display...")
# test_lcd_instance.clear()
# time.sleep(1)

# # New test for flipped display functionality
# print("\n--- Embedded LCD Flipped Display Test ---")
# print("Embedded test: Initializing LCD in flipped mode")
# flipped_lcd_instance = LCD(flipped=True)
# print("Embedded test: Displaying 'Flipped Line 1' on logical line 1 (should appear on physical line 2)")
# flipped_lcd_instance.message("Flipped Line 1", line=1)
# print("Embedded test: Displaying 'Flipped Line 2' on logical line 2 (should appear on physical line 1)")
# flipped_lcd_instance.message("Flipped Line 2", line=2)
# time.sleep(3)

# print("Embedded test: Toggling flipped state to False using set_flipped()")
# flipped_lcd_instance.set_flipped(False)
# flipped_lcd_instance.clear()
# flipped_lcd_instance.message("Normal Line 1", line=1)
# flipped_lcd_instance.message("Normal Line 2", line=2)
# time.sleep(3)
# flipped_lcd_instance.clear()
# print("--- Embedded LCD Flipped Display Test Completed ---")


# print("--- Embedded LCD test completed successfully ---")
