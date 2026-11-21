import time
from machine import Pin

# Onboard LED Raspberry Pi Pico terhubung ke GPIO 25
led = Pin(25, Pin.OUT)

print("Raspberry Pi Pico MicroPython siap di Wokwi!")

while True:
    led.toggle()
    print("LED status:", led.value())
    time.sleep(1)
