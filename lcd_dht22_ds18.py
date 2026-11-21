from machine import Pin, I2C
from time import sleep, sleep_ms
import dht, onewire, ds18x20

class LCD:
    def __init__(self, i2c, addr=0x27):
        self.i2c, self.addr = i2c, addr
        sleep_ms(50)
        for c in (0x33, 0x32, 0x28, 0x0C, 0x06, 0x01):
            self.cmd(c)

    def _pulse(self, d):
        self.i2c.writeto(self.addr, bytes([d | 0x0C]))
        self.i2c.writeto(self.addr, bytes([(d | 0x08) & ~0x04]))

    def _send(self, v, m):
        self._pulse((v & 0xF0) | m)
        self._pulse(((v << 4) & 0xF0) | m)

    def cmd(self, v):
        self._send(v, 0)
        sleep_ms(2)

    def puts(self, text, row):
        self.cmd(0x80 | (0x40 * row))
        for ch in "{:<16}".format(text):
            self._send(ord(ch), 1)

lcd = LCD(I2C(0, sda=Pin(20), scl=Pin(21)))
d = dht.DHT22(Pin(17))
ds = ds18x20.DS18X20(onewire.OneWire(Pin(16)))
rom = ds.scan()[0]
sleep(2)

while True:
    d.measure()
    ds.convert_temp()
    sleep_ms(750)
    lcd.puts("DHT:{:.1f}C H:{:.0f}%".format(d.temperature(), d.humidity()), 0)
    lcd.puts("DS18B20:{:.1f}C".format(ds.read_temp(rom)), 1)
    sleep(1)