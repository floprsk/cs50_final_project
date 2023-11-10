#!/usr/bin/python3
# coding: utf8
# boot.py
import RPi.GPIO as GPIO
import sys
import time

# PINS FESTLEGEN
relais1 = 12


# GPIO SETUP
GPIO.setmode(GPIO.BCM)
GPIO.setup(relais1, GPIO.OUT)

# GPIO DEAKTIVIEREN
GPIO.output(relais1, 1)
