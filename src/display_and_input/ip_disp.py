import socket
from LCD import LCD

"""
file runs on boot and shows the ip address of the device
"""

def get_ip_address():
    """
    Retrieves the local IP address of the device.

    This function attempts to determine the primary IP address by
    connecting to a well-known external host (Google's DNS server).
    It does not send any data, but uses the socket's local address
    after establishing a connection.

    Returns:
        str: The IP address as a string, or "N/A" if the IP address
             cannot be determined (e.g., no network connection).
    """
    rotation = ["",".", "..", "..."]
    
    lcd = LCD()
    message_count = 0

    while True:
        
    
        try:
            # Create a UDP socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Connect to a public IP address (Google's DNS server) on a common port.
            # This doesn't send data, but forces the OS to choose the
            # appropriate network interface and its IP address for the route.
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]
            s.close()

            lcd.message("Connected", line=1)
            lcd.message(ip_address, line=2)
            # Keep running to maintain display
            return ip_address

        except socket.error:
            message_count = (message_count + 1) % 4
            message = "No Network" + rotation[message_count]
            lcd.message(message, line=1, duration=0.4)
        except Exception as e:
            # Catch any other unexpected errors
            print(f"Error getting IP address: {e}")
            import time
            time.sleep(5)  # Wait before retrying

if __name__ == "__main__":
    get_ip_address()

    