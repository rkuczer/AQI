import http.client
import json
import sqlite3

# Function to parse the JSON data
def parse_json(json_data):
    parsed_data = json.loads(json_data)
    return parsed_data

# Connect to the SQLite database
conn = sqlite3.connect('AQI_data.db')
cursor = conn.cursor()

# Create a table to store AQI data if it doesn't exist already
cursor.execute('''CREATE TABLE IF NOT EXISTS AirQuality (
                    id INTEGER PRIMARY KEY,
                    city_name TEXT,
                    country_code TEXT,
                    lon REAL,
                    lat REAL,
                    state_code TEXT,
                    timezone TEXT,
                    aqi INTEGER,
                    co REAL,
                    datetime TEXT,
                    no2 REAL,
                    o3 REAL,
                    pm10 REAL,
                    pm25 REAL,
                    so2 REAL,
                    timestamp_local TEXT,
                    timestamp_utc TEXT,
                    ts INTEGER,
                    UNIQUE(datetime)
                )''')

# API request to get data
conn_api = http.client.HTTPSConnection("air-quality.p.rapidapi.com")
headers = {
    'X-RapidAPI-Key': "3e350aa343msh88296d28e123221p16a4c8jsn0a6951d24206",
    'X-RapidAPI-Host': "air-quality.p.rapidapi.com"
}
conn_api.request("GET", "/history/airquality?lon=-71.347&lat=42.278", headers=headers)
res = conn_api.getresponse()
json_data = res.read().decode("utf-8")

# Parse the JSON data
parsed_data = parse_json(json_data)

# Insert data into the database if datetime value doesn't exist already
for entry in parsed_data['data']:
    try:
        cursor.execute('''INSERT INTO AirQuality (
                            city_name, country_code, lon, lat, state_code, timezone,
                            aqi, co, datetime, no2, o3, pm10, pm25, so2, timestamp_local,
                            timestamp_utc, ts
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                       (parsed_data['city_name'], parsed_data['country_code'], parsed_data['lon'],
                        parsed_data['lat'], parsed_data['state_code'], parsed_data['timezone'],
                        entry['aqi'], entry['co'], entry['datetime'], entry['no2'], entry['o3'],
                        entry['pm10'], entry['pm25'], entry['so2'], entry['timestamp_local'],
                        entry['timestamp_utc'], entry['ts']))
    except sqlite3.IntegrityError:
        print("Some Data has been ignored " + str(entry))
        # Ignore if the datetime value already exists in the database
        pass

# Commit the transaction and close the connection
conn.commit()
conn.close()

#print("Data inserted successfully into the database.")
