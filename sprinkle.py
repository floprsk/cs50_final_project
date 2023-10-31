import time
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
import RPi.GPIO as GPIO

# Raspi Configs
SPI_PORT = 0
SPI_DEVICE = 0
mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))
port = 12
GPIO.setmode(GPIO.BCM)


GPIO.setup(port, GPIO.OUT)
GPIO.output(port, 0)
time.sleep(10) # 10s watering is equal to ca. 200ml water in my setup
GPIO.output(port, 1)
GPIO.cleanup()
