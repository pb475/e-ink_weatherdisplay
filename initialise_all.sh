#!/bin/bash

cd "/home/weatherpi/Documents/e-ink_weatherdisplay/"

source "venv/bin/activate"

screen -S grabdata -dm python3 grab_accuweather_data.py
screen -S drawdata -dm sudo python3 draw.py