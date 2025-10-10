from gpiozero import Button, RotaryEncoder
from signal import pause

# Switch on GPIO17 (active low, since tied to GND)
switch = Button(26, pull_up=True)

# Rotary encoder on GPIO27 (A) and GPIO22 (B)
encoder = RotaryEncoder(a=6, b=27, max_steps=0)

def pressed():
    print("Switch pressed!")

def long_press():
    print("Long button press recognised")

def rotated():
    print(f"Encoder steps: {encoder.steps}")

switch.when_pressed = pressed
switch.when_held = long_press
switch.hold_time = 1  # Hold time in seconds
encoder.when_rotated = rotated

print("Listening... press Ctrl+C to exit")
pause()
