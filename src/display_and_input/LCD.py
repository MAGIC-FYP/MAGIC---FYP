import smbus
import time



#TODO:
# - Add a function to clear the LCD
# - Add a function to display a message on the LCD that scrolls properly
# - Add higher level function that handles conversion of menu into LCD

    def __init__(self, pi_rev = 2, i2c_addr = 0x27, backlight = True):

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

        # Open I2C interface
        if pi_rev == 2:
            # Rev 2 Pi uses 1
            self.bus = smbus.SMBus(1)
        elif pi_rev == 1:
            # Rev 1 Pi uses 0
            self.bus = smbus.SMBus(0)
        else:
            raise ValueError('pi_rev param must be 1 or 2')

        # Initialise display
        self.lcd_byte(0x33, self.LCD_CMD) # 110011 Initialise
        self.lcd_byte(0x32, self.LCD_CMD) # 110010 Initialise
        self.lcd_byte(0x06, self.LCD_CMD) # 000110 Cursor move direction
        self.lcd_byte(0x0C, self.LCD_CMD) # 001100 Display On,Cursor Off, Blink Off
        self.lcd_byte(0x28, self.LCD_CMD) # 101000 Data length, number of lines, font size
        self.lcd_byte(0x01, self.LCD_CMD) # 000001 Clear display

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

    def message(self, string, line=1, scroll=False, scroll_speed=0.3):
        # Display message string on LCD line 1 or 2
        if line == 1:
            lcd_line = self.LCD_LINE_1
        elif line == 2:
            lcd_line = self.LCD_LINE_2
        else:
            raise ValueError('line number must be 1 or 2')

        # Pad or trim the string to at least LCD_WIDTH
        if len(string) < self.LCD_WIDTH:
            string = string.ljust(self.LCD_WIDTH, " ")

        if scroll and len(string) > self.LCD_WIDTH:
            # Add spaces to the end for smooth scrolling off the display
            scroll_text = string + " " * self.LCD_WIDTH
            for i in range(len(scroll_text) - self.LCD_WIDTH + 1):
                window = scroll_text[i:i + self.LCD_WIDTH]
                self.lcd_byte(lcd_line, self.LCD_CMD)
                for char in window:
                    self.lcd_byte(ord(char), self.LCD_CHR)
                time.sleep(scroll_speed)
        else:
            # Display as much as fits, padded or trimmed
            display_text = string[:self.LCD_WIDTH].ljust(self.LCD_WIDTH, " ")
            self.lcd_byte(lcd_line, self.LCD_CMD)
            for char in display_text:
                self.lcd_byte(ord(char), self.LCD_CHR)

    def clear(self):
        # clear LCD display
        self.lcd_byte(0x01, self.LCD_CMD)
