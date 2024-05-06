
def get_api_key_from_file():
    # READ IN API KEY
    with open('my_accuweather_api_key.txt', 'r') as file:
        api_key = file.read().strip()
        return api_key


def read_lat_lon():
    import csv
    # ----------------------------------------------------------
    # READ IN LOCATION AND LATITUDE AND LONGITUDE
    # Open the CSV file
    with open('my_lat_lon.csv', 'r') as file:
        # Create a CSV reader object
        reader = csv.reader(file)
        # Iterate over each row in the CSV file
        next(reader) # Skip the header row
        for row in reader:
            # Access the data in each row
            location = row[0]
            latitude = float(row[1])
            longitude = float(row[2])

    return dict(location=location, latitude=latitude, longitude=longitude)