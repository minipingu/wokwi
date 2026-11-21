import network
import urequests
from machine import Pin, I2C
from time import sleep, sleep_ms, sleep_us, ticks_ms, ticks_diff
import dht, onewire, ds18x20

# ================= KONFIGURASI BLYNK =================
BLYNK_TEMPLATE_ID = "TMPL6_x-zaxIf"
BLYNK_TEMPLATE_NAME = "wokwi"
BLYNK_AUTH_TOKEN = "4ytGcA0SvWURuZc0UNJ0kQorDXY1Ycjd"

# Mapping Virtual Pin Blynk:
# V0: Suhu DHT22 (°C)
# V1: Kelembaban DHT22 (%)
# V2: Suhu DS18B20 (°C)

# ================= DRIVER LCD I2C =================
class LCD:
    def __init__(self, i2c, addr=0x27):
        self.i2c, self.addr = i2c, addr
        sleep_ms(50)
        for c in (0x33, 0x32, 0x28, 0x0C, 0x06, 0x01):
            self.cmd(c)

    def _pulse(self, d):
        try:
            self.i2c.writeto(self.addr, bytes([d | 0x0C]))
            sleep_us(2)
            self.i2c.writeto(self.addr, bytes([(d | 0x08) & ~0x04]))
            sleep_us(50)
        except OSError:
            pass

    def _send(self, v, m):
        self._pulse((v & 0xF0) | m)
        self._pulse(((v << 4) & 0xF0) | m)

    def cmd(self, v):
        self._send(v, 0)
        sleep_ms(2)

    def puts(self, text, row):
        try:
            self.cmd(0x80 | (0x40 * row))
            for ch in "{:<16}".format(text):
                self._send(ord(ch), 1)
        except OSError:
            pass

# Inisialisasi Perangkat Keras (Gunakan freq=100000 agar komunikasi I2C stabil)
i2c = I2C(0, sda=Pin(20), scl=Pin(21), freq=100000)
lcd = LCD(i2c)
d = dht.DHT22(Pin(17))
ds = ds18x20.DS18X20(onewire.OneWire(Pin(16)))

# Tampilan Awal di LCD
lcd.puts("Connecting WiFi.", 0)
lcd.puts("Wokwi-GUEST", 1)

# Koneksi ke Wi-Fi Wokwi
print("Menghubungkan ke WiFi Wokwi-GUEST...")
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("Wokwi-GUEST", "")

while not wlan.isconnected():
    sleep_ms(200)
    print(".", end="")

print("\nWiFi Terhubung! IP:", wlan.ifconfig()[0])
lcd.puts("WiFi Connected!", 0)
lcd.puts(wlan.ifconfig()[0], 1)
sleep(2)

# Deteksi Sensor DS18B20
roms = ds.scan()
rom = roms[0] if roms else None
if not rom:
    print("Peringatan: Sensor DS18B20 tidak terdeteksi!")

last_blynk_send = 0
BLYNK_INTERVAL = 2000  # Interval kirim ke Blynk: 3 detik

# Loop Utama
while True:
    # 1. Baca DHT22
    try:
        d.measure()
        d_temp = d.temperature()
        d_hum = d.humidity()
    except Exception as e:
        d_temp, d_hum = 0.0, 0.0
        print("Gagal membaca DHT22:", e)

    # 2. Baca DS18B20
    try:
        ds.convert_temp()
        sleep_ms(750)
        ds_temp = ds.read_temp(rom) if rom else 0.0
    except Exception as e:
        ds_temp = 0.0
        print("Gagal membaca DS18B20:", e)

    # 3. Perbarui Tampilan LCD (dengan penanganan error bus I2C)
    try:
        lcd.puts("DHT:{:.1f}C H:{:.0f}%".format(d_temp, d_hum), 0)
        lcd.puts("DS18B20:{:.1f}C".format(ds_temp), 1)
    except Exception as e:
        print("LCD error:", e)

    # 4. Kirim Data ke Blynk IoT via REST API
    now = ticks_ms()
    if ticks_diff(now, last_blynk_send) >= BLYNK_INTERVAL:
        last_blynk_send = now
        try:
            # Menggunakan host region sgp1.blynk.cloud
            url = "http://sgp1.blynk.cloud/external/api/batch/update?token={}&v0={:.1f}&v1={:.1f}&v2={:.1f}".format(
                BLYNK_AUTH_TOKEN, d_temp, d_hum, ds_temp
            )
            res = urequests.get(url)
            print("Blynk update (V0={:.1f}, V1={:.1f}, V2={:.1f}) -> Status: {}".format(
                d_temp, d_hum, ds_temp, res.status_code
            ))
            res.close()
        except Exception as e:
            print("Error kirim ke Blynk:", e)

    sleep(1)
