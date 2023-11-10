import sqlite3
from datetime import datetime

import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
import RPi.GPIO as GPIO

# Raspi Configs
SPI_PORT = 0
SPI_DEVICE = 0
mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))
port = 12
GPIO.setmode(GPIO.BCM)

# Get data from humidity sensor as percentage


def sensor_info():
    hum = mcp.read_adc(0)
    per = ((590-int(hum))*100) / 314
    # 590 = minimal humidity
    # 277 = maximal humidity
    # --> 314 = difference
    return int(per)


con = sqlite3.connect("watering_users.db")
cur = con.cursor()

humidity = sensor_info()
timestamp = datetime.datetime.now()
formatted_timestamp = timestamp.strftime("%d-%m-%Y %H:%M:%S")
cur.execute("INSERT INTO data (time, humidity_per) VALUES (?, ?)",
            [formatted_timestamp, humidity])
con.commit()
con.close()
