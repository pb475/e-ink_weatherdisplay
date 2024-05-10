#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys, os
import logging
import time
from datetime import timedelta, date, datetime
import traceback
from PIL import Image,ImageDraw,ImageFont
import import_pickles as ip
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.combining import OrTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio


# Set the mode of the script
construction=False # set to True for construction mode
testing=True # set to False for live display
screensavepath = 'screen_image/img2display.png'
funmode = True # set to False for boring mode


# Set the path to the e-ink display library
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'e-ink_weatherdisplay/e-Paper/RaspberryPi_JetsonNano/python/pic/')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'e-ink_weatherdisplay/e-Paper/RaspberryPi_JetsonNano/python/lib/')
if os.path.exists(libdir):
    sys.path.append(libdir)
else:
    raise ValueError(str(libdir)+'path does not exist')
# import the e-ink display library
from waveshare_epd import epd7in5


# Set the logging level
logging.basicConfig(level=logging.DEBUG)

# Set the font sizes
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
    overlay_image = overlay_image.resize((width, height), Image.NEAREST)

    def white2transparent(img):
        datas = img.getdata()
        newData = []
        for item in datas:
            if item[0] == 255 and item[1] == 255 and item[2] == 255:  # finding white colour by its RGB value
                # storing a transparent value when we find a black colour
                newData.append((255, 255, 255, 0))
            else:
                newData.append(item)  # other colours remain unchanged
        img.putdata(newData)
        return img

    overlay_image = white2transparent(overlay_image)


    # Paste the overlay image onto the existing imagege
    Mimage.paste(overlay_image, (x, y), overlay_image)
    if construction: draw.rectangle((x, y, x+width, y+height), outline=0)
    return


def place_infobox(Himage,draw,today,hourly_df,x,y,squaresize=64,fontsize=24):
    if construction: draw.rectangle((x, y, x+squaresize*2+buffer*2, y+squaresize), outline=0, fill = 255)

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
    draw.text((x, y+squaresize//2), 'MIN: '+str(mintemp), font = font[32], fill = 0)

    # place the moon icon
    y=y+squaresize+buffer
    place_moon(Himage,draw,today["Moon"]["Age"],x,y,squaresize=squaresize,fontsize=fontsize)

    # place the precipitation probability
    precipitation_probability = round(hourly_df["PrecipitationProbability"].max())
    place_precipitation(Himage,draw,precipitation_probability, x,y+squaresize+buffer,squaresize=squaresize,fontsize=18)

    # place the UV index
    uvindex = today["UVIndex"]["Value"]
    place_uvindex(Himage,draw,uvindex,x+squaresize+2*buffer,y,squaresize=squaresize,fontsize=64)

    # place the pollen
    # maxpollen = max(today["Tree"]["Value"],today["Grass"]["Value"],today["Ragweed"]["Value"])
    # place_pollen(Himage,draw,maxpollen,x+64+2*buffer,y+64+buffer,squaresize=64,fontsize=24)

    place_wind(Himage,draw,hourly_df["Wind"],x+squaresize+2*buffer,y+squaresize+buffer,squaresize=squaresize,fontsize=24)

    # place the sunrise and sunset
    place_sunrise(Himage,draw,x,y+squaresize*2+2*buffer,squaresize=squaresize,fontsize=22)
    place_sunset(Himage,draw,x+squaresize+2*buffer,y+squaresize*2+2*buffer,squaresize=squaresize,fontsize=22)

    return


def today_rectangle(Himage,draw,x,y,daily_df,hourly_df,current_df):
    if construction: draw.rectangle((x, y, splitpos-2*buffer, today_tomorrow_split-buffer), outline=0)

    iconsize = 128

    x1=buffer
    y1=y+64+64+32
    place_icon(Himage, draw, ip.whichicon(daily_df["IconDay"].iloc[0],iconsize=128,day=True), x1, y1, iconsize, iconsize)

    x1=x1+iconsize+2*buffer
    place_icon(Himage, draw, ip.whichicon(daily_df["IconNight"].iloc[0],iconsize=128,day=False), x1, y1, iconsize, iconsize)

    place_infobox(Himage,draw,daily_df.iloc[0],hourly_df,x+buffer+280,y+2)

    return


def day_rectangle(Himage,draw,x,y,day,daystring):
    if construction: draw.rectangle((x, y, splitpos-2*buffer, epd.height-buffer), outline=0, fill = 255)
    draw.text((x+buffer, y-2), daystring, font = font[36])

    iconsize = 96
    y1 = y+44
    place_icon(Himage, draw, ip.whichicon(day["IconDay"],iconsize=128,day=True), x, y1, iconsize, iconsize)
    x1 = x+96+2*buffer
    place_icon(Himage, draw, ip.whichicon(day["IconNight"],iconsize=128,day=False), x1, y1, iconsize, iconsize)

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
    y1 = y+64+64+32-buffer
    draw.rectangle((x, y, x1, y1), outline=255, fill=255)
    if construction: draw.rectangle((x, y, x1, y1), outline=0)
    draw_HHMM(draw,x,y-16,112)
    draw_date(draw,x+buffer,y+80+buffer,56)
    return


def place_smallweathericon(Himage,draw,row,x,y,squaresize,iconsize):
    if construction: draw.rectangle((x, y, x+squaresize, y+squaresize), outline=0)
    day = row["IsDaylight"] # True or False for day or night
    place_icon(Himage, draw, ip.whichicon(row["WeatherIcon"],iconsize=iconsize,day=day), x, y, iconsize, iconsize)
    return


def place_temperature(Himage,draw,temperature,x,y,squaresize,fontsize):
    temperature = round(temperature)
    if temperature < 10:
        place_icon(Himage, draw, 'icons/pack1/'+str(squaresize)+'/bmp/045-thermometer-4.bmp', x, y, squaresize, squaresize)
    elif temperature < 20:
        place_icon(Himage, draw, 'icons/pack1/'+str(squaresize)+'/bmp/048-thermometer-2.bmp', x-18, y, squaresize, squaresize)
    else:
        place_icon(Himage, draw, 'icons/pack1/'+str(squaresize)+'/bmp/050-thermometer-4.bmp', x, y, squaresize, squaresize)
    draw.text((x+32, y+36), str(temperature), font = font[fontsize], fill = 0)
    if construction: draw.rectangle((x, y, x+squaresize, y+squaresize), outline=0)
    return


def place_moon(Himage,draw,moon_age,x,y,squaresize,fontsize):
    # Moon_age should be the days since new moon
    if construction: draw.rectangle((x, y, x+squaresize, y+squaresize), outline=0)

    moon_phase = [''] * 8 # create an empty list
    moon_phase[0]='025-moon-phase-7.bmp' # New moon
    moon_phase[1]='024-moon-phase-6.bmp' # Waxing crescent
    moon_phase[2]='063-moon-phase-5.bmp' # First quarter - half moon
    moon_phase[3]='022-moon-phase-4.bmp' # Waxing gibbous
    moon_phase[4]='021-moon-phase-3.bmp' # Full moon
    moon_phase[5]='019-moon-phase-2.bmp' # Waning gibbous
    moon_phase[6]='018-moon-phase-1.bmp' # Last quarter - half moon
    moon_phase[7]='017-moon-phase.bmp' # Waning crescent

    # Set the icon pack
    iconpack = 'icons/pack1/'+str(squaresize)+'/bmp/'
    # Set the moon phase (approximate)
    def place_moonphase(file):
        place_icon(Himage, draw, file, x, y, squaresize, squaresize)
        return
    match moon_age:
        case 0: # New moon
            place_moonphase(iconpack+moon_phase[0])
        case 1|2|3|4|5: # Waxing crescent
            place_moonphase(iconpack+moon_phase[1])
        case 7|8: # First quarter - half moon
            place_moonphase(iconpack+moon_phase[2])
        case 9|10|11|12|13: # Waxing gibbous
            place_moonphase(iconpack+moon_phase[3])
        case 14|15: # Full moon
            place_moonphase(iconpack+moon_phase[4])
        case 16|17|18|19|20: # Waning gibbous
            place_moonphase(iconpack+moon_phase[5])
        case 21|22|23: # Last quarter - half moon
            place_moonphase(iconpack+moon_phase[6])
        case 24|25|26|27|28|29|30: # Waning crescent
            place_moonphase(iconpack+moon_phase[7])
        case _: # UNKNOWN ERROR, HOW DID WE GET HERE?
            place_icon(Himage, draw, iconpack+'99-interrogation-mark.bmp', x, y, squaresize, squaresize)
    return


def place_pollen(Himage,draw,maxpollen,x,y,squaresize,fontsize):
    if construction: draw.rectangle((x, y, x+squaresize, y+squaresize), outline=0)
    if maxpollen<3: # low - no protection required
        place_icon(Himage, draw, 'icons/pack1/'+str(squaresize)+'/bmp/029-pollen-2.bmp', x, y, squaresize, squaresize)
    elif maxpollen<4:   # medium - some protection advised
        place_icon(Himage, draw, 'icons/pack1/'+str(squaresize)+'/bmp/028-pollen-1.bmp', x, y, squaresize, squaresize)
    elif maxpollen<=6:   # high - protection required
        place_icon(Himage, draw, 'icons/pack1/'+str(squaresize)+'/bmp/027-pollen.bmp', x, y, squaresize, squaresize)
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
        place_icon(Himage, draw, 'icons/pack1/'+str(squaresize)+'/bmp/036-wind-2.bmp', x, y, squaresize, squaresize)
    elif maxwind<15: # high - windy
        place_icon(Himage, draw, 'icons/pack1/'+str(squaresize)+'/bmp/035-wind-1.bmp', x, y, squaresize, squaresize)
    elif maxwind<20: # very high - very windy
        place_icon(Himage, draw, 'icons/pack1/'+str(squaresize)+'/bmp/033-wind.bmp', x, y, squaresize, squaresize)
    else: # extreme - very windy
        place_icon(Himage, draw, 'icons/pack1/'+str(squaresize)+'/bmp/031-tornado.bmp', x, y, squaresize, squaresize)
    return


def place_sunrise(Himage,draw,x,y,squaresize,fontsize):
    from suntime import Sun
    from read_from_files import read_lat_lon
    import pytz

    latlondict = read_lat_lon()

    sun = Sun(latlondict["latitude"], latlondict["longitude"])
    tz_london = pytz.timezone('Europe/London')

    # Get today's sunrise and sunset in UTC
    today_sr = sun.get_sunrise_time().astimezone(tz_london)
    today_ss = sun.get_sunset_time().astimezone(tz_london)

    # print('Today at lat-lon the sun raised at {} and get down at {} UTC'.format(today_sr.strftime('%H:%M'), today_ss.strftime('%H:%M')))

    if construction: draw.rectangle((x, y, x+squaresize, y+squaresize+18), outline=0)
    place_icon(Himage, draw, 'icons/pack1/'+str(squaresize)+'/bmp/059-sunrise.bmp', x, y, squaresize, squaresize)
    draw.text((x+squaresize//2, y+squaresize), today_sr.strftime('%H:%M'), font = font[fontsize], fill = 0, anchor="mt")
    return


def place_sunset(Himage,draw,x,y,squaresize,fontsize):
    from suntime import Sun
    from read_from_files import read_lat_lon
    import pytz

    latlondict = read_lat_lon()

    sun = Sun(latlondict["latitude"], latlondict["longitude"])
    tz_london = pytz.timezone('Europe/London')

    # Get today's sunrise and sunset in UTC
    today_sr = sun.get_sunrise_time().astimezone(tz_london)
    today_ss = sun.get_sunset_time().astimezone(tz_london)
    # print('Today lat-lon the sun raised at {} and get down at {} UTC'.format(today_sr.strftime('%H:%M'), today_ss.strftime('%H:%M')))

    if construction: draw.rectangle((x, y, x+squaresize, y+squaresize+18), outline=0)
    place_icon(Himage, draw, 'icons/pack1/'+str(squaresize)+'/bmp/060-sunset.bmp', x, y, squaresize, squaresize)
    draw.text((x+squaresize//2, y+squaresize), today_ss.strftime('%H:%M'), font = font[fontsize], fill = 0, anchor="mt")
    return


def place_precipitation(Himage,draw,probability,x,y,squaresize,fontsize):
    if construction: draw.rectangle((x, y, x+squaresize, y+squaresize), outline=0)
    place_icon(Himage, draw, 'icons/pack1/'+str(squaresize)+'/bmp/012-drop-1.bmp', x, y, 64, 64)
    draw.text((x+squaresize//2, y+2*squaresize//3), str(probability)+"%", font = font[fontsize], fill = 0, anchor="mm")
    return


def place_uvindex(Himage,draw,uvindex,x,y,squaresize=64,fontsize=24):
    if construction: draw.rectangle((x, y, x+squaresize, y+squaresize), outline=0)
    if uvindex<3: # low - no protection required
        pass
    elif uvindex<6: #medium - some protection advised
        place_icon(Himage, draw, 'icons/pack1/'+str(squaresize)+'/bmp/007-uv-1.bmp', x, y, squaresize, squaresize)
        pass
    elif uvindex<8: # high - protection required
        place_icon(Himage, draw, 'icons/pack1/'+str(squaresize)+'/bmp/008-uv-2.bmp', x, y, squaresize, squaresize)
    elif uvindex<11: # very high - extra protection required
        place_icon(Himage, draw, 'icons/pack1/'+str(squaresize)+'/bmp/009-uv-3.bmp', x, y, squaresize, squaresize)
    else: # extreme - extra protection required
        place_icon(Himage, draw, 'icons/pack1/'+str(squaresize)+'/bmp/009-uv-3.bmp', x, y, squaresize, squaresize)
    return


def days_from_now(n):
    return date.today() + timedelta(n)

def dashed_horizontal_line(draw,x1,x2,y1,length=4):
    for x in range(x1, x2, length):
        draw.line([(x, y1), (x + length//2, y1)], fill=0)
    return

def dashed_vertical_line(draw,y1,y2,x1,length=4):
    for y in range(y1, y2, length):
        draw.line([(x1, y), (x1, y+length//2)], fill=0)
    return

# create basic epd class for testing
class epd_Cls(object):
    def __init__(self):
        # constructor code here
        self.height = 480
        self.width = 800
    def clear(self):
        Himage = Image.new('1', (epd.width, epd.height), 255)  # 255: clear the frame (make white)
        epd.display(epd.getbuffer(Himage))
    def getbuffer(self,Himage):
        Himage.save(screensavepath, 'bmp')
        return Himage
    def init(self):
        pass
    def display(self,Himage):
        return
    def display_Partial(self,Himage, a, b, width, height):
        Himage.save(screensavepath, 'bmp')
        return

# Main script
try:
    logging.info("epd7in5 e-ink weather display")

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
    today_tomorrow_split=(2*epd.height)//3+buffer


    # Define the display functions to be called by the scheduler hourly
    def hourly_display():
        # Drawing on the Horizontal image
        logging.info("Drawing hourly image...")
        # Create the image
        Himage = Image.new('1', (epd.width, epd.height), 255)  # 255: clear the frame
        draw = ImageDraw.Draw(Himage)

        # draw the date rectangle
        date_rectangle(draw,buffer,buffer)

        # Load the pickled data
        current_df,daily_df,hourly_df,requests_remaining=ip.load_all_pickles()
        if any([current_df is None,daily_df is None,hourly_df is None,requests_remaining is None]):
            logging.error("No forecast data, printing error to screen")
            place_icon(Himage, draw, 'icons/pack1/128/bmp/098-warning-sign.bmp', buffer, buffer+128+64, 128, 128)
            draw.text((2*buffer+128+24, buffer+128+64+12), "No forecast data available", font = font[36],fill=0)
            draw.text((2*buffer+128+24, buffer+2*128+12), "Recommendation: check logs", font = font[36],fill=0)
            # input()
            epd.display(epd.getbuffer(Himage))
            return

        # draw the left/right split line
        draw.rectangle((splitpos-buffer, buffer, splitpos, epd.height-buffer), outline=0, fill = 0) # draw the split line left/right
        # draw the top/bottom split line
        draw.rectangle((buffer, today_tomorrow_split, splitpos-2*buffer, today_tomorrow_split+buffer), outline=0, fill = 0) # draw the split line today/tomorrow
        # draw today rectangle
        today_rectangle(Himage,draw,buffer,buffer,daily_df,hourly_df,current_df)
        # draw tomorrow rectangle
        y1 = today_tomorrow_split+buffer*2
        day_rectangle(Himage,draw,buffer,y1,daily_df.iloc[1],'Tomorrow')
        # draw next day rectangle
        x1 = splitpos//2+buffer
        day_rectangle(Himage,draw,x1,y1,daily_df.iloc[2],days_from_now(2).strftime('%A'))

        # ----------------------------------
        # Draw the next few hours
        num_hours = 6
        hourly_height = inner_height//6
        squaresize = 64
        for counter in range(num_hours):
            row = hourly_df.iloc[counter] # extract the row from the dataframe

            the_time=row["DateTime"].partition("t")[2][0:5] # extract the time from the DateTime string

            xpos = splitpos+buffer*2
            ypos = 2*buffer+hourly_height*(counter)

            if construction: draw.rectangle((xpos,ypos,epd.width-buffer,ypos+hourly_height-buffer),outline=0)
            clock_offset = 4
            clockheight,clockwidth,(clockx,clocky)=draw_theHHMM(draw,x=xpos,y=ypos+clock_offset,the_time=the_time,fontsize=48)


            # draw the first item
            x1pos = xpos+clockwidth+buffer
            x2pos = x1pos+squaresize+2*buffer
            x3pos = x2pos+squaresize+3*buffer
            place_temperature(Himage,draw,row['RealFeelTemperature']['Value'],x3pos,ypos,squaresize,24) # draw this first for overlaps
            place_precipitation(Himage,draw,row['PrecipitationProbability'],x1pos,ypos,squaresize,18)
            place_smallweathericon(Himage,draw,row,x2pos,ypos,squaresize,squaresize)
            pass # end of loop

        def draw_bmp_scene(Himage,draw,x,y):
            # draw the bmp icon
            bmp_size = 24
            hrs = int(datetime.now().strftime('%H'))

            date = int(datetime.now().strftime('%d'))

            def place_member(imgname,x,y,bmp_size=24):
                place_icon(Himage,draw,'icons/pack2/'+str(bmp_size)+'/bmp/'+imgname,x,y,bmp_size,bmp_size)
                return
            def scene0():
                place_member('009-rat.bmp',x, y)
                place_member('061-platter.bmp',x+bmp_size, y+10,16)
                pass
            def scene1():
                place_member('005-goose.bmp',x, y)
                place_member('001-heart.bmp',x+bmp_size+buffer, y)
                place_member('008-mouse-1_flipped.bmp',x+2*bmp_size+buffer*2, y+7)
                return
            def scene2():
                place_member('008-mouse-1_flipped.bmp',x, y+10)
                place_member('011-yarn.bmp',x+bmp_size+buffer*2, y+4)
                return
            def scene3():
                place_member('054-toad.bmp',x, y)
                place_member('053-frog_flipped.bmp',x+bmp_size+buffer, y+3)
                return
            def scene4():
                place_member('054-toad.bmp',x, y)
                place_member('051-marshmallows.bmp',x+bmp_size-buffer, y)
                place_member('049-bonfire-1.bmp',x+2*bmp_size, y+3)
                place_member('051-marshmallows_flipped.bmp',x+3*bmp_size, y)
                place_member('053-frog_flipped.bmp',x+4*bmp_size-buffer, y+3)
                return
            def scene5():
                place_member('081-ant_flipped.bmp',x, y+2)
                place_member('081-ant_flipped.bmp',x+bmp_size, y+2)
                place_member('081-ant_flipped.bmp',x+2*bmp_size, y+2)
                place_member('081-ant_flipped.bmp',x+3*bmp_size, y+2)
                place_member('081-ant_flipped.bmp',x+4*bmp_size, y+2)
                return
            def scene6():
                place_member('086-praying-mantis.bmp',x, y+2)
                place_member('042-wine-glass.bmp',x+bmp_size-1, y-3)
                place_member('086-praying-mantis_flipped.bmp',x+2*bmp_size-2, y+2)
                return
            def scene7():
                place_member('072-mushrooms.bmp',x+4, y+2)
                place_member('073-mushroom.bmp',x+bmp_size, y)
                place_member('071-fungi_flipped.bmp',x+2*bmp_size, y+2)
                place_member('072-mushrooms_flipped.bmp',x+3*bmp_size-3, y+4)
                return
            def scene8():
                place_member('097-confetti.bmp',x, y)
                place_member('098-dance_flipped.bmp',x+bmp_size, y)
                place_member('098-dance.bmp',x+2*bmp_size, y)
                place_member('097-confetti.bmp',x+3*bmp_size, y)
                return
            def scene9():
                place_member('005-goose.bmp',x-bmp_size, y)
                place_member('044-music-wave_flipped.bmp',x+buffer, y-3)
                place_member('043-radio-antenna.bmp',x+bmp_size+buffer, y+1)
                place_member('044-music-wave.bmp',x+2*bmp_size+buffer, y-3)
                place_member('008-mouse-1.bmp',x+3*bmp_size+2*buffer, y+10)
                return

            # now choose which scene to display
            match int(datetime.now().strftime('%d'))%10:
                case 0:
                    scene0()
                case 1:
                    scene1()
                case 2:
                    scene2()
                case 3:
                    scene3()
                case 4:
                    scene4()
                case 5:
                    scene5()
                case 6:
                    scene6()
                case 7:
                    scene7()
                case 8:
                    scene8()
                case 9:
                    scene9()
                case _:
                    pass


        bmp_size = 24
        from suntime import Sun
        from read_from_files import read_lat_lon
        import pytz
        latlondict = read_lat_lon()
        sun = Sun(latlondict["latitude"], latlondict["longitude"])
        tz_london = pytz.timezone('Europe/London')
        # Get today's sunrise and sunset in current time zone
        today_ss = sun.get_sunset_time().astimezone(tz_london).replace(tzinfo=None)
        if datetime.now()<today_ss: # if before sunset
            x1 = buffer+24
        else: # if after sunset
            x1 = 138+24+buffer
        if funmode: draw_bmp_scene(Himage,draw,x1,today_tomorrow_split-bmp_size)

        # Display the image with a full refresh
        epd.display(epd.getbuffer(Himage))
        #
        return

    def cleanup_and_hourly_display():
        flicker_time = 3 #seconds
        if testing: flicker_time = 0.001

        logging.info("Performing screen cleanup...")

        # Create the image
        for j in range(15):
            Himage = Image.new('1', (epd.width, epd.height), 0)  # 255: clear the frame
            epd.display(epd.getbuffer(Himage))
            time.sleep(flicker_time)
            # Clear the display
            epd.clear()
            time.sleep(flicker_time)

        hourly_display()

        return

    # Define the display functions to be called by the scheduler minutely
    def minutely_display():
        logging.info("Drawing minutely image...")
        # Load the image from savepath
        Himage = Image.open(screensavepath)
        draw = ImageDraw.Draw(Himage)
        # over-draw the date rectangle
        date_rectangle(draw,buffer,buffer)
        # Display the image with a partial refresh
        epd.display_Partial(epd.getbuffer(Himage), 0, 0, epd.width, epd.height)
        #
        return



    #------------
    # Display the image
    cleanup_and_hourly_display() # display the hourly display on script run

    #------------
    # This is the bit which triggers
    # Create a scheduler
    logging.info("Creating scheduler...")
    scheduler = AsyncIOScheduler()
    scheduler.start()
    # Add the special hourly job which also does the display cleaning
    logging.info("Adding jobs to scheduler...")
    trigger = OrTrigger([CronTrigger(hour='00',minute='00') ])
    scheduler.add_job(cleanup_and_hourly_display, trigger, misfire_grace_time=10)
    # Add the hourly job
    trigger = OrTrigger([CronTrigger(hour='01-23',minute='00') ])
    scheduler.add_job(hourly_display, trigger, misfire_grace_time=10)
    # Add the minutely job
    trigger = OrTrigger([CronTrigger(minute='01-59')])
    scheduler.add_job(minutely_display, trigger, misfire_grace_time=10)

    logging.info("running loop...")
    # Keep the script running
    try:
        asyncio.get_event_loop().run_forever()
    except SystemExit:
        logging.info("SystemExit")
        pass
    except KeyboardInterrupt:
        logging.info("ctrl + c:")
        if not testing:
            epd7in5.epdconfig.module_exit(cleanup=True)
            exit()

except IOError as e:
    logging.info(e)

except KeyboardInterrupt:
    logging.info("ctrl + c:")
    if not testing:
        epd7in5.epdconfig.module_exit(cleanup=True)
        exit()
