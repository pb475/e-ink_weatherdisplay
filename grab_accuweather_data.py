"""Example of usage."""

import logging
import sys


libdir = 'accuweather/'
sys.path.append(libdir)

logging.basicConfig(level=logging.DEBUG)


async def get_data_from_accuweather(latitude,longitude,api_key):
    from aiohttp import ClientError, ClientSession
    from accuweather import (
        AccuWeather,
        ApiError,
        InvalidApiKeyError,
        InvalidCoordinatesError,
        RequestsExceededError,
    )
    """Run main function."""
    async with ClientSession() as websession:
        try:
            print(api_key,latitude,longitude)
            accuweather = AccuWeather(
                api_key,
                websession,
                latitude=latitude,
                longitude=longitude,
                language="gb",
            )
            current_conditions = await accuweather.async_get_current_conditions()
            forecast_daily = await accuweather.async_get_daily_forecast(
                days=5, metric=True
            )
            forecast_hourly = await accuweather.async_get_hourly_forecast(
                hours=12, metric=True
            )
        except (
            ApiError,
            InvalidApiKeyError,
            InvalidCoordinatesError,
            ClientError,
            RequestsExceededError,
        ) as error:
            print(f"Error: {error}")
            # return None #return None if there is an error
        else:
            # print(f"Location: {accuweather.location_name} ({accuweather.location_key})")
            # print(f"Requests remaining: {accuweather.requests_remaining}")
            # print(f"Current: {current_conditions}")
            # print(f"Forecast: {forecast_daily}")
            # print(f"Forecast hourly: {forecast_hourly}")
            return accuweather.requests_remaining,current_conditions,forecast_daily,forecast_hourly



def main():
    import asyncio
    import pickle
    import pandas as pd
    from read_from_files import get_api_key_from_file,read_lat_lon

    latlondict = read_lat_lon() #grab latitude and longitude from file and store in variables

    try:
        loop = asyncio.new_event_loop()
        requests_remaining,current_conditions,forecast_daily,forecast_hourly = loop.run_until_complete(get_data_from_accuweather(latitude=latlondict["latitude"],
                                                                                                longitude=latlondict["longitude"],
                                                                                                api_key=get_api_key_from_file()))
        loop.close()
        print('API PING SUCCESSFUL '+str(requests_remaining)+" requests remaining.")
    except:
        raise ValueError

    print('Converting to dataframes')
    current_conditions_df = pd.DataFrame(current_conditions)
    forecast_daily_df = pd.DataFrame(forecast_daily)
    forecast_hourly_df = pd.DataFrame(forecast_hourly)

    # SAVE THE DATA TO FILE
    # Save accuweather to a files
    print('pickling requests_remaining')
    with open('data/requests_remaining.pkl', 'wb') as file:
        pickle.dump(requests_remaining, file)
    print('pickling current_conditions')
    current_conditions_df.to_pickle('data/current_conditions_df.pkl')
    print('pickling forecast_daily')
    forecast_daily_df.to_pickle('data/forecast_daily_df.pkl')
    print('pickling forecast_hourly')
    forecast_hourly_df.to_pickle('data/forecast_hourly_df.pkl')

    return



from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.combining import OrTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
# This is the bit which triggers
cron = CronTrigger(minute='58') #trigger 10 minutes to the hour
trigger = OrTrigger([cron])
# Create a scheduler
scheduler = AsyncIOScheduler()
scheduler.start()
scheduler.add_job(main, trigger)

# Keep the script running
try:
    asyncio.get_event_loop().run_forever()
except (KeyboardInterrupt, SystemExit):
    pass

