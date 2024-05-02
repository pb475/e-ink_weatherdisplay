import datapoint
import csv

# ----------------------------------------------------------
# STEP 1: READ IN API KEY, LOCATION, LATITUDE AND LONGITUDE
with open('my_datapoint_api_key.txt', 'r') as file:
    api_key = file.read().strip()
    print('api key:')
    print(api_key)

# ----------------------------------------------------------
# STEP 2: READ IN LOCATION AND LATITUDE AND LONGITUDE
# Open the CSV file
with open('my_lat_lon.csv', 'r') as file:
    # Create a CSV reader object
    reader = csv.reader(file)

    # Iterate over each row in the CSV file
    next(reader) # Skip the header row
    for row in reader:
        # Access the data in each row
        # print(row[0])
        print(row[:])
        location = row[0]
        latitude = row[1]
        longitude = row[2]

# ----------------------------------------------------------
# STEP 3: GET THE WEATHER DATA
# Create connection to DataPoint with your API key
conn = datapoint.connection(api_key=api_key)
# Get the nearest site for my latitude and longitude
site = conn.get_nearest_forecast_site(latitude=latitude,longitude=longitude)
# Get a forecast for my nearest site with 3 hourly timesteps
forecast = conn.get_forecast_for_site(site.location_id, "3hourly")
# Get the current timestep from the forecast
current_timestep = forecast.now()
# Print out the site and current weather
print(site.name + "-" + current_timestep.weather.text)