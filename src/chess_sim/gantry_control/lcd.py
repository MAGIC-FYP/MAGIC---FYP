import lgpio
import time

def test_display_power():
    print("Testing display power and basic functions...")
    
    try:
        addr = 0x27
        # Open I2C connection
        handle = lgpio.i2c_open(2, addr)
        print("✓ Connected to display at 0x3C")
        
        # Test 1: Turn display ON with maximum contrast
        print("Turning display ON with max contrast...")
        lgpio.i2c_write_byte_data(handle, addr, 0x00)  # Control byte
        lgpio.i2c_write_byte_data(handle, addr, 0xAF)  # Display ON
        
        # Set maximum contrast
        lgpio.i2c_write_byte_data(handle, addr, 0x00)  # Control byte
        lgpio.i2c_write_byte_data(handle, addr, 0x81)  # Set contrast command
        lgpio.i2c_write_byte_data(handle, addr, 0x00)  # Control byte
        lgpio.i2c_write_byte_data(handle, addr, 0xFF)  # Max contrast
        
        time.sleep(2)
        
        # Test 2: Try to fill entire display with white
        print("Filling display with white pixels...")
        
        # Set addressing mode and range
        lgpio.i2c_write_byte_data(handle, addr, 0x00)  # Control byte
        lgpio.i2c_write_byte_data(handle, addr, 0x21)  # Set column address
        lgpio.i2c_write_byte_data(handle, addr, 0x00)  # Control byte
        lgpio.i2c_write_byte_data(handle, addr, 0x7F)  # End column (127)
        
        lgpio.i2c_write_byte_data(handle, addr, 0x00)  # Control byte
        lgpio.i2c_write_byte_data(handle, addr, 0x22)  # Set page address
        lgpio.i2c_write_byte_data(handle, addr, 0x00)  # Control byte
        lgpio.i2c_write_byte_data(handle, addr, 0x03)  # End page (3)
        
        # Switch to data mode and fill with white
        lgpio.i2c_write_byte_data(handle, addr, 0x40)  # Data mode
        for i in range(512):  # 128x32 display = 512 bytes
            lgpio.i2c_write_byte_data(handle, addr, 0xFF)  # All pixels ON
        
        print("Display should be completely WHITE now")
        time.sleep(3)
        
        # Test 3: Clear display
        print("Clearing display...")
        lgpio.i2c_write_byte_data(handle, 0x3C, 0x40)  # Data mode
        for i in range(512):
            lgpio.i2c_write_byte_data(handle, 0x3C, 0x00)  # All pixels OFF
        
        lgpio.i2c_close(handle)
        print("Test completed!")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test_display_power()