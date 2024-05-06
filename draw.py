#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os

import import_pickles as ip

current_df,daily_df,hourly_df,requests_remaining=ip.load_all_pickles()

picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'e-ink_weatherdisplay/e-Paper/RaspberryPi_JetsonNano/python/pic/')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'e-ink_weatherdisplay/e-Paper/RaspberryPi_JetsonNano/python/lib/')

construction=True
screensavepath = 'screen_image/img2display.png'

if os.path.exists(libdir):
    sys.path.append(libdir)
else:
    raise ValueError(str(libdir)+'path does not exist')

import logging
from waveshare_epd import epd7in5
import time
from PIL import Image,ImageDraw,ImageFont
import traceback
from datetime import datetime

from datetime import timedelta, date



logging.basicConfig(level=logging.DEBUG)


font = {18: ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 18),
        20: ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 20),
        22: ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 22),
        24: ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 24),
        26: ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 26),
        28: ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 28),
        30: ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 30),
        32: ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 32),
        34: ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 34),
        36: ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 36),
        40: ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 40),
        48: ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 48),
        56: ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 56),
        64: ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 64),
        72: ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 72),
        80: ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 80),
        96: ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 96),
        112: ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 112),
        128: ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 128)
        }


def draw_theHHMM(draw,x,y,the_time,fontsize):
    # draw.rectangle((x, y, x+xlength, y+ylength), outline=0, fill = 255)
    draw.text((x, y), the_time, font = font[fontsize], fill = 0)
    bbox = draw.textbbox((x, y), "24:00", font=font[fontsize])
    if construction: draw.rectangle(bbox, outline="black")
    clockheight = bbox[3]-bbox[1]
    clockwidth = bbox[2]-bbox[0]
    return clockheight, clockwidth, (bbox[0],bbox[1])


def place_icon(Mimage, draw, iconpath, x, y, width, height):
    # Open the image to overlay
    overlay_image = Image.open(iconpath).convert("RGBA")
    # Resize the overlay image to fit the desired size
    overlay_image = overlay_image.resize((width, height), Image.HAMMING)
    # Paste the overlay image onto the existing image
    Mimage.paste(overlay_image, (x, y), overlay_image)
    if construction: draw.rectangle((x, y, x+width, y+height), outline=0)
    return


def place_infobox(Himage,draw,today,hourly_df,x,y,squaresize=64,fontsize=24):
    if construction: draw.rectangle((x, y, x+squaresize*2+buffer*2, y+squaresize+buffer*1), outline=0, fill = 255)

    # place the temperature min and max
    # method 1 for finding the max and min temperatures
    maxtemp = 0
    for row in hourly_df["RealFeelTemperature"]:
        if row["Value"]>maxtemp:
            maxtemp = row["Value"]
    maxtemp = round(maxtemp)
    #
    mintemp = 1e32
    for row in hourly_df["RealFeelTemperature"]:
        if row["Value"]<mintemp:
            mintemp = row["Value"]
    mintemp = round(mintemp)
    # method 2 for finding the max and min temperatures
    # maxtemp = round(today["RealFeelTemperatureMax"]['Value'])
    # mintemp = round(today["RealFeelTemperatureMin"]['Value'])
    # now place the max and min temperatures
    draw.text((x, y), 'MAX: '+str(maxtemp), font = font[32], fill = 0)
    draw.text((x, y+36), 'MIN: '+str(mintemp), font = font[32], fill = 0)

    # place the moon icon
    y=y+squaresize+buffer*2
    place_moon(Himage,draw,today["Moon"]["Age"],x,y,squaresize=squaresize,fontsize=fontsize)

    # place the precipitation probability
    precipitation_probability = round(hourly_df["PrecipitationProbability"].sum()/hourly_df["PrecipitationProbability"].size)
    place_precipitation(Himage,draw,precipitation_probability, x,y+squaresize+buffer,squaresize=squaresize,fontsize=18)

    # place the UV index
    uvindex = today["UVIndex"]["Value"]
    place_uvindex(Himage,draw,uvindex,x+squaresize+2*buffer,y,squaresize=squaresize,fontsize=64)

    # place the pollen
    # maxpollen = max(today["Tree"]["Value"],today["Grass"]["Value"],today["Ragweed"]["Value"])
    # place_pollen(Himage,draw,maxpollen,x+64+2*buffer,y+64+buffer,squaresize=64,fontsize=24)

    place_wind(Himage,draw,hourly_df["Wind"],x+squaresize+2*buffer,y+squaresize+buffer,squaresize=squaresize,fontsize=24)

    # place the sunrise and sunset
    place_sunrise(Himage,draw,x,y+squaresize*2+2*buffer,squaresize=squaresize,fontsize=24)
    place_sunset(Himage,draw,x+squaresize+2*buffer,y+squaresize*2+2*buffer,squaresize=squaresize,fontsize=24)

    return

def today_rectangle(Himage,draw,x,y,daily_df,hourly_df,current_df):
    if construction: draw.rectangle((x, y, splitpos-2*buffer, today_tomorrow_split-buffer), outline=0)

    iconsize = 128

    x1=buffer
    y1=y+136+buffer*4
    place_icon(Himage, draw, ip.whichicon(daily_df["IconDay"].iloc[0],iconsize=128,day=True), x1, y1, iconsize, iconsize)

    x1=x1+128+buffer
    place_icon(Himage, draw, ip.whichicon(daily_df["IconNight"].iloc[0],iconsize=128,day=False), x1, y1, iconsize, iconsize)

    place_infobox(Himage,draw,daily_df.iloc[0],hourly_df,x+buffer+280,y)

    return


def day_rectangle(Himage,draw,x,y,day,daystring):
    if construction: draw.rectangle((x, y, splitpos-2*buffer, epd.height-buffer), outline=0, fill = 255)
    draw.text((x, y), daystring, font = font[36])

    iconsize = 96
    y1 = y+48
    place_icon(Himage, draw, ip.whichicon(day["IconDay"],iconsize=96,day=True), x, y1, iconsize, iconsize)
    x1 = x+96+buffer
    place_icon(Himage, draw, ip.whichicon(day["IconNight"],iconsize=96,day=False), x1, y1, iconsize, iconsize)

    return


def nextday_rectangle(Himage,draw,x,y,nextday):

    if construction: draw.rectangle((x, y, splitpos-2*buffer, epd.height-buffer), outline=0, fill = 255)

    draw.text((x, y), days_from_now(2).strftime('%A'), font = font[36], fill = 0)

    iconsize = 96
    y1 = y+50
    place_icon(Himage, draw, ip.whichicon(nextday["IconDay"],iconsize=96,day=True), x, y1, iconsize, iconsize)
    x1 = x+96+buffer
    place_icon(Himage, draw, ip.whichicon(nextday["IconNight"],iconsize=96,day=False), x1, y1, iconsize, iconsize)

    return


def date_rectangle(draw,x,y):
    def draw_HHMM(draw,x,y,fontsize):
        draw.text((x, y), time.strftime('%H:%M'), font = font[fontsize], fill = 0)
        bbox = draw.textbbox((x, y), "24:00", font=font[fontsize])
        if construction: draw.rectangle(bbox, outline="black")
        clockheight = bbox[3]-bbox[1]
        clockwidth = bbox[2]-bbox[0]
        return clockheight, clockwidth, (bbox[0],bbox[1])
    def draw_date(draw,x,y,fontsize):
        draw.text((x, y), time.strftime('%d %b %-y'), font = font[fontsize], fill = 0)
        return
    clockheight, clockwidth, (dummy1,dummy2) = draw_HHMM(draw,x,y-16,112) # run once to get the clockheight and clockwidth
    x1 = x+clockwidth
    y1 = y+128+buffer*3
    draw.rectangle((x, y, x1, y1), outline=255, fill=255)
    if construction: draw.rectangle((x, y, x1, y1), outline=0)
    draw_HHMM(draw,x,y-16,112)
    draw_date(draw,x,y+80+buffer,56)
    return


def place_smallweathericon(Himage,draw,row,x,y,squaresize,iconsize):
    if construction: draw.rectangle((x, y, x+squaresize, y+squaresize), outline=0)
    day = row["IsDaylight"] # True or False for day or night
    place_icon(Himage, draw, ip.whichicon(row["WeatherIcon"],iconsize=iconsize,day=day), x, y, iconsize, iconsize)
    return


def place_temperature(Himage,draw,temperature,x,y,squaresize,fontsize):
    temperature = round(temperature)
    if temperature < 11:
        place_icon(Himage, draw, 'icons/pack1-'+str(squaresize)+'/png/075-thermometer-4.png', x, y, squaresize, squaresize)
    elif temperature < 19:
        place_icon(Himage, draw, 'icons/pack1-'+str(squaresize)+'/png/056-thermometer-1.png', x-18, y, squaresize, squaresize)
    else:
        place_icon(Himage, draw, 'icons/pack1-'+str(squaresize)+'/png/078-thermometer-6.png', x, y, squaresize, squaresize)
    draw.text((x+32, y+36), str(temperature), font = font[fontsize], fill = 0)
    if construction: draw.rectangle((x, y, x+squaresize, y+squaresize), outline=0)
    return


def place_moon(Himage,draw,moon_age,x,y,squaresize,fontsize):
    # Moon_age should be the days since new moon
    if construction: draw.rectangle((x, y, x+squaresize, y+squaresize), outline=0)
    if moon_age==0: #TODO: this needs to be checked and possibly corrected
        place_icon(Himage, draw, 'icons/pack1-'+str(squaresize)+'/png/064-moon-phase-1.png', x, y, squaresize, squaresize)
    elif moon_age<7:
        place_icon(Himage, draw, 'icons/pack1-'+str(squaresize)+'/png/065-moon-phase-2.png', x, y, squaresize, squaresize)
    elif moon_age<14:
        place_icon(Himage, draw, 'icons/pack1-'+str(squaresize)+'/png/066-moon-phase-3.png', x, y, squaresize, squaresize)
    elif moon_age<21:
        place_icon(Himage, draw, 'icons/pack1-'+str(squaresize)+'/png/067-moon-phase-4.png', x, y, squaresize, squaresize)
    elif moon_age<28:
        place_icon(Himage, draw, 'icons/pack1-'+str(squaresize)+'/png/068-moon-phase-5.png', x, y, squaresize, squaresize)
    elif moon_age==28:
        place_icon(Himage, draw, 'icons/pack1-'+str(squaresize)+'/png/069-moon-phase-6.png', x, y, squaresize, squaresize)
    else: #this should not trigger!
        place_icon(Himage, draw, 'icons/pack1-'+str(squaresize)+'/png/064-moon-phase-1.png', x, y, squaresize, squaresize)
    return

def place_pollen(Himage,draw,maxpollen,x,y,squaresize,fontsize):
    if construction: draw.rectangle((x, y, x+squaresize, y+squaresize), outline=0)
    if maxpollen<3: # low - no protection required
        place_icon(Himage, draw, 'icons/pack1-'+str(squaresize)+'/png/059-pollen.png', x, y, squaresize, squaresize)
    elif maxpollen<4:   # medium - some protection advised
        place_icon(Himage, draw, 'icons/pack1-'+str(squaresize)+'/png/060-pollen-1.png', x, y, squaresize, squaresize)
    elif maxpollen<=6:   # high - protection required
        place_icon(Himage, draw, 'icons/pack1-'+str(squaresize)+'/png/060-pollen-1.png', x, y, squaresize, squaresize)
    return

def place_wind(Himage,draw,wind_data,x,y,squaresize,fontsize):
    maxwind = 0
    for datum in wind_data:
        if datum["Speed"]["Value"]>maxwind:
            maxwind = datum["Speed"]["Value"]

    maxwind = round(maxwind)
    if maxwind<5: # low - little wind
        pass
    elif maxwind<10: # medium - some wind
        place_icon(Himage, draw, 'icons/pack1-'+str(squaresize)+'/png/072-wind-1.png', x, y, squaresize, squaresize)
    elif maxwind<15: # high - windy
        place_icon(Himage, draw, 'icons/pack1-'+str(squaresize)+'/png/072-wind-1.png', x, y, squaresize, squaresize)
    elif maxwind<20: # very high - very windy
        place_icon(Himage, draw, 'icons/pack1-'+str(squaresize)+'/png/072-wind-1.png', x, y, squaresize, squaresize)
    else: # extreme - very windy
        place_icon(Himage, draw, 'icons/pack1-'+str(squaresize)+'/png/072-wind-1.png', x, y, squaresize, squaresize)
    return


def place_sunrise(Himage,draw,x,y,squaresize,fontsize):
    from suntime import Sun
    from read_from_files import read_lat_lon

    latlondict = read_lat_lon()

    sun = Sun(latlondict["latitude"], latlondict["longitude"])

    # Get today's sunrise and sunset in UTC
    today_sr = sun.get_sunrise_time()
    today_ss = sun.get_sunset_time()
    # print('Today at lat-lon the sun raised at {} and get down at {} UTC'.format(today_sr.strftime('%H:%M'), today_ss.strftime('%H:%M')))

    if construction: draw.rectangle((x, y, x+squaresize, y+squaresize+18), outline=0)
    place_icon(Himage, draw, 'icons/pack1-'+str(squaresize)+'/png/007-sunrise.png', x, y, squaresize, squaresize)
    draw.text((x+2, y+58), today_sr.strftime('%H:%M'), font = font[fontsize], fill = 0)
    return


def place_sunset(Himage,draw,x,y,squaresize,fontsize):
    from suntime import Sun
    from read_from_files import read_lat_lon

    latlondict = read_lat_lon()

    sun = Sun(latlondict["latitude"], latlondict["longitude"])

    # Get today's sunrise and sunset in UTC
    today_sr = sun.get_sunrise_time()
    today_ss = sun.get_sunset_time()
    # print('Today lat-lon the sun raised at {} and get down at {} UTC'.format(today_sr.strftime('%H:%M'), today_ss.strftime('%H:%M')))

    if construction: draw.rectangle((x, y, x+squaresize, y+squaresize+18), outline=0)
    place_icon(Himage, draw, 'icons/pack1-'+str(squaresize)+'/png/046-sunset.png', x, y, squaresize, squaresize)
    draw.text((x+2, y+58), today_ss.strftime('%H:%M'), font = font[fontsize], fill = 0)
    return


def place_precipitation(Himage,draw,probability,x,y,squaresize,fontsize):
    if construction: draw.rectangle((x, y, x+squaresize, y+squaresize), outline=0)
    place_icon(Himage, draw, 'icons/pack1-'+str(squaresize)+'/png/040-drop-1.png', x, y, 64, 64)
    # bbox = draw.textbbox((x, y), "100%", font=font[fontsize])
    # if construction: draw.rectangle(bbox, outline="black")
    # percheight = bbox[3]-bbox[1]
    # percwidth = bbox[2]-bbox[0]
    draw.text((x+squaresize//4-2, y+30), str(probability)+"%", font = font[fontsize], fill = 0)
    return


def place_uvindex(Himage,draw,uvindex,x,y,squaresize=64,fontsize=24):
    if construction: draw.rectangle((x, y, x+squaresize, y+squaresize), outline=0)
    if uvindex<3: # low - no protection required
        pass
    elif uvindex<6: #medium - some protection advised
        place_icon(Himage, draw, 'icons/pack1-'+str(squaresize)+'/png/051-uv.png', x, y, squaresize, squaresize)
        pass
    elif uvindex<8: # high - protection required
        place_icon(Himage, draw, 'icons/pack1-'+str(squaresize)+'/png/051-uv.png', x, y, squaresize, squaresize)
    elif uvindex<11: # very high - extra protection required
        place_icon(Himage, draw, 'icons/pack1-'+str(squaresize)+'/png/051-uv.png', x, y, squaresize, squaresize)
    else: # extreme - extra protection required
        place_icon(Himage, draw, 'icons/pack1-'+str(squaresize)+'/png/051-uv.png', x, y, squaresize, squaresize)
    return

def days_from_now(n):
    return date.today() + timedelta(n)

# create basic epd class for testing
class epd_Cls(object):
    def __init__(self):
        # constructor code here
        self.height = 480
        self.width = 800

    def clear(self):
        if os.path.exists(screensavepath):
            os.remove(screensavepath)
    def getbuffer(self,Himage):
        Himage.save(screensavepath, 'PNG')
        return Himage
    def init(self):
        pass
    def display(self,Himage):
        return
    def display_Partial(self,Himage, a, b, width, height):
        Himage.save(screensavepath, 'PNG')
        return



try:
    logging.info("epd7in5 Demo")

    testing=True
    if testing:
        logging.info("RUNNING TESTING CONFIGURATION")
        logging.info("init epd class")
        epd = epd_Cls() #initialise the cls
    else:
        logging.info("RUNNING LIVE CONFIGURATION")
        logging.info("init epd class")
        epd = epd7in5.EPD()
        logging.info("init and Clear")
        epd.init()
        epd.Clear()

    # set some things
    buffer=5
    splitpos = 5*epd.width//9
    inner_height = epd.height-2*buffer
    today_tomorrow_split=2*epd.height//3

    # Drawing on the Horizontal image
    logging.info("1.Drawing on the Horizontal image...")

    def hourly_display():
        # Create the image
        Himage = Image.new('1', (epd.width, epd.height), 255)  # 255: clear the frame
        draw = ImageDraw.Draw(Himage)
        # draw the left/right split line
        draw.rectangle((splitpos-buffer, buffer, splitpos, epd.height-buffer), outline=0, fill = 0) # draw the split line left/right
        # draw the top/bottom split line
        draw.rectangle((buffer, today_tomorrow_split, splitpos-2*buffer, today_tomorrow_split+buffer), outline=0, fill = 0) # draw the split line today/tomorrow
        # draw the date rectangle
        date_rectangle(draw,buffer,buffer)
        # draw today rectangle
        today_rectangle(Himage,draw,buffer,buffer,daily_df,hourly_df,current_df)
        # draw tomorrow rectangle
        day_rectangle(Himage,draw,buffer,today_tomorrow_split+buffer,daily_df.iloc[1],'Tomorrow')
        # draw next day rectangle

        day_rectangle(Himage,draw,6*buffer+96*2,today_tomorrow_split+buffer,daily_df.iloc[2],days_from_now(2).strftime('%A'))
        # ----------------------------------
        # Draw the next few hours
        num_hours = 6
        hourly_height = inner_height//6
        for counter in range(num_hours):
            row = hourly_df.iloc[counter] # extract the row from the dataframe
            #-----------
            the_time=row["DateTime"].partition("t")[2][0:5] # extract the time from the DateTime string

            xpos = splitpos+buffer
            ypos = buffer+hourly_height*counter

            if construction: draw.rectangle((xpos,ypos,epd.width-buffer,ypos+hourly_height-buffer),outline=0)
            clock_offset = 4
            clockheight,clockwidth,(clockx,clocky)=draw_theHHMM(draw,x=xpos,y=ypos+clock_offset,the_time=the_time,fontsize=48)

            squaresize = 64
            # draw the first item
            x1pos = xpos+clockwidth+2*buffer
            x2pos = x1pos+squaresize+2*buffer
            x3pos = x2pos+squaresize+2*buffer
            place_temperature(Himage,draw,row['RealFeelTemperature']['Value'],x3pos,ypos,squaresize,24) # draw this first for overlaps
            place_precipitation(Himage,draw,row['PrecipitationProbability'],x1pos,ypos,squaresize,18)
            place_smallweathericon(Himage,draw,row,x2pos,ypos,squaresize,squaresize)

        # Display the image with a full refresh
        epd.display(epd.getbuffer(Himage))



    def minutely_display():
        # Load the image from savepath
        Himage = Image.open(screensavepath)
        draw = ImageDraw.Draw(Himage)
        # over-draw the date rectangle
        date_rectangle(draw,buffer,buffer)
        # Display the image with a partial refresh
        epd.display_Partial(epd.getbuffer(Himage), 0, 0, epd.width, epd.height)


    #------------
    # Display the image
    hourly_display() # display the hourly display on script run

    # Set up the scheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.combining import OrTrigger
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    import asyncio
    # This is the bit which triggers
    # Create a scheduler
    scheduler = AsyncIOScheduler()
    scheduler.start()
    # Add the hourly job
    trigger = OrTrigger([CronTrigger(minute='00') ]) #trigger 10 minutes to the hour
    scheduler.add_job(hourly_display, trigger)
    # Add the minutely job
    trigger = OrTrigger([CronTrigger(minute='01-59')])
    scheduler.add_job(minutely_display, trigger)

    # Keep the script running
    try:
        asyncio.get_event_loop().run_forever()
    except SystemExit:
        pass
    except KeyboardInterrupt:
        logging.info("ctrl + c:")
        epd7in5.epdconfig.module_exit(cleanup=True)
        exit()

except IOError as e:
    logging.info(e)

except KeyboardInterrupt:
    logging.info("ctrl + c:")
    epd7in5.epdconfig.module_exit(cleanup=True)
    exit()
