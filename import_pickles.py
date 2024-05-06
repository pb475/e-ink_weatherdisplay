import pickle

def loadpickle(file_path):
    # Open the pkl file in read mode
    with open(file_path, 'rb') as file:
        # Load the contents of the pkl file
        data = pickle.load(file)
    return data


def whichicon(weathercode, iconsize, day=True):
    import os
    prefix = "icons/pack1-"+str(iconsize)+"/png/"
    iconfile = prefix + number2icon(weathercode,day=day)
    if not os.path.exists(iconfile):
        iconfile = "icons/question.png"
    return iconfile


def number2icon(number,day=True):
    import pandas as pd

    # Set the default to unknown
    icon='Unknown'
    iconfile='021-question.png'

    # Read the csv file
    if day:
        df = pd.read_csv("icons/day_iconpaths.csv")
    else: # it is night
        df = pd.read_csv("icons/night_iconpaths.csv")

    # Find the icon
    if df.loc[df['Num'] == number] is not None:
        iconfile = df.loc[df['Num'] == number]["Iconpath"].values[0]

    # return icon,
    return iconfile

    # This is from accuweather API documentation https://developer.accuweather.com/weather-icons
    # Num   Icon 	                    Day 	Night 	Text
    # 1 	Sunny 	                    Yes 	No 	    Sunny
    # 2 	Mostly Sunny 	            Yes 	No 	    Mostly Sunny
    # 3 	Partly Sunny 	            Yes 	No 	    Partly Sunny
    # 4 	Intermittent Clouds         Yes 	No 	    Intermittent Clouds
    # 5 	Hazy Sunshine 	            Yes 	No 	    Hazy Sunshine
    # 6 	Mostly Cloudy 	            Yes 	No 	    Mostly Cloudy
    # 7 	Cloudy 	                    Yes 	Yes 	Cloudy
    # 8 	Dreary 	                    Yes 	Yes 	Dreary (Overcast)
    # 11 	Fog 	                    Yes 	Yes 	Fog
    # 12 	Showers 	                Yes 	Yes 	Showers
    # 13 	Mostly Cloudy w/ Showers 	Yes 	No 	    Mostly Cloudy w/ Showers
    # 14 	Partly Sunny w/ Showers 	Yes 	No 	    Partly Sunny w/ Showers
    # 15 	T-Storms 	                Yes 	Yes 	T-Storms
    # 16 	Mostly Cloudy w/ T-Storms 	Yes 	No 	    Mostly Cloudy w/ T-Storms
    # 17 	Partly Sunny w/ T-Storms 	Yes 	No 	    Partly Sunny w/ T-Storms
    # 18 	Rain 	                    Yes 	Yes 	Rain
    # 19 	Flurries 	                Yes 	Yes 	Flurries
    # 20 	Mostly Cloudy w/ Flurries 	Yes 	No 	    Mostly Cloudy w/ Flurries
    # 21 	Partly Sunny w/ Flurries 	Yes 	No 	    Partly Sunny w/ Flurries
    # 22 	Snow 	                    Yes 	Yes 	Snow
    # 23 	Mostly Cloudy w/ Snow 	    Yes 	No 	    Mostly Cloudy w/ Snow
    # 24 	Ice 	                    Yes 	Yes 	Ice
    # 25 	Sleet 	                    Yes 	Yes 	Sleet
    # 26 	Freezing Rain 	            Yes 	Yes 	Freezing Rain
    # 29 	Rain and Snow 	            Yes 	Yes 	Rain and Snow
    # 30 	Hot 	                    Yes 	Yes 	Hot
    # 31 	Cold 	                    Yes 	Yes 	Cold
    # 32 	Windy 	                    Yes 	Yes 	Windy
    # 33 	Clear 	                    No 	    Yes 	Clear
    # 34 	Mostly Clear 	            No 	    Yes 	Mostly Clear
    # 35 	Partly Cloudy 	            No 	    Yes 	Partly Cloudy
    # 36 	Intermittent Clouds         No 	    Yes 	Intermittent Clouds
    # 37 	Hazy Moonlight 	            No 	    Yes 	Hazy Moonlight
    # 38 	Mostly Cloudy 	            No 	    Yes 	Mostly Cloudy
    # 39 	Partly Cloudy w/ Showers 	No 	    Yes 	Partly Cloudy w/ Showers
    # 40 	Mostly Cloudy w/ Showers 	No 	    Yes 	Mostly Cloudy w/ Showers
    # 41 	Partly Cloudy w/ T-Storms 	No 	    Yes 	Partly Cloudy w/ T-Storms
    # 42 	Mostly Cloudy w/ T-Storms 	No 	    Yes 	Mostly Cloudy w/ T-Storms
    # 43 	Mostly Cloudy w/ Flurries 	No 	    Yes 	Mostly Cloudy w/ Flurries
    # 44 	Mostly Cloudy w/ Snow 	    No 	    Yes 	Mostly Cloudy w/ Snow


def load_all_pickles():
    prefix = 'data/'
    current_conditions_df = loadpickle(prefix+'current_conditions_df.pkl')
    forecast_daily_df = loadpickle(prefix+'forecast_daily_df.pkl')
    forecast_hourly_df = loadpickle(prefix+'forecast_hourly_df.pkl')
    requests_remaining = loadpickle(prefix+'requests_remaining.pkl')

    return current_conditions_df,forecast_daily_df,forecast_hourly_df,requests_remaining


def epoch2datetime(epoch):
    import datetime
    dt = datetime.datetime.fromtimestamp(epoch)
    return dt
