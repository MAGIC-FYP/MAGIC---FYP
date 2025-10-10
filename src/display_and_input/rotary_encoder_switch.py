from gpiozero import Button, RotaryEncoder
from signal import pause

# Switch on GPIO17 (active low, since tied to GND)
switch = Button(17, pull_up=True)

# Rotary encoder on GPIO27 (A) and GPIO22 (B)
encoder = RotaryEncoder(a=27, b=22, max_steps=0)

def pressed():
    print("Switch pressed!")

def rotated():
    print(f"Encoder steps: {encoder.steps}")

switch.when_pressed = pressed
encoder.when_rotated = rotated

print("Listening... press Ctrl+C to exit")
pause()
