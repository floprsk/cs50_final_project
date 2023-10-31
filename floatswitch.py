import time
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
import RPi.GPIO as GPIO

# Raspi Configs
SPI_PORT = 0
SPI_DEVICE = 0
mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))
port = 12


try:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(21, GPIO.IN)
    GPIO.setup(port, GPIO.OUT)
    is_full = GPIO.input(21)

    if is_full == 0:
        GPIO.output(port,1)
    print("YASALAAAAAAAAAAAAAAMMEEEEEE")

except Exception as e:
        print(f"Fehler in float_switch: {e}")
    



#GPIO.cleanup()
