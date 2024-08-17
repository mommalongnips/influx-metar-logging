import os
import subprocess
import sys
import requests
import time
from dotenv import load_dotenv

# Load environment variables from a .env file if present
load_dotenv()

# Function to install missing packages
def install_package(package_name):
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package_name])
    except subprocess.CalledProcessError:
        print(f"Failed to install package: {package_name}")
        sys.exit(1)

# Check and install required packages
try:
    import requests
except ImportError:
    print("requests package not found. Installing...")
    install_package('requests')

# Fetch environment variables
CHECKWX_API_KEY = os.getenv('CHECKWX_API_KEY')
INFLUXDB_API_KEY = os.getenv('INFLUXDB_API_KEY')
INFLUXDB_HOST = os.getenv('INFLUXDB_HOST')
INFLUXDB_PORT = os.getenv('INFLUXDB_PORT', '8086')
INFLUXDB_BUCKET = os.getenv('INFLUXDB_BUCKET')
INFLUXDB_ORG = os.getenv('INFLUXDB_ORG')
AIRPORTS = os.getenv('AIRPORTS', 'KBJC,KFNL').split(',')
INTERVAL = int(os.getenv('INTERVAL', '300'))

# Check if all required environment variables are set
if not CHECKWX_API_KEY:
    print("Error: CHECKWX_API_KEY is not set.")
    sys.exit(1)

if not INFLUXDB_API_KEY:
    print("Error: INFLUXDB_API_KEY is not set.")
    sys.exit(1)

if not INFLUXDB_HOST:
    print("Error: INFLUXDB_HOST is not set.")
    sys.exit(1)

if not INFLUXDB_BUCKET:
    print("Error: INFLUXDB_BUCKET is not set.")
    sys.exit(1)

if not INFLUXDB_ORG:
    print("Error: INFLUXDB_ORG is not set.")
    sys.exit(1)

if INTERVAL < 60:
    print("Warning: INTERVAL is set to less than 60 seconds. Ensure you have a CheckWX subscription to avoid exceeding rate limits.")

# InfluxDB URL with org and bucket variables
INFLUXDB_URL = f'http://{INFLUXDB_HOST}:{INFLUXDB_PORT}/api/v2/write?org={INFLUXDB_ORG}&bucket={INFLUXDB_BUCKET}&precision=s'

# Function to fetch METAR data for multiple airports from CheckWX API
def fetch_metar_data(airport_codes):
    headers = {
        'X-API-Key': CHECKWX_API_KEY
    }
    # Join the airport codes into a comma-separated string
    airports_str = ",".join(airport_codes)
    response = requests.get(f'https://api.checkwx.com/metar/{airports_str}/decoded', headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data and data['data']:
            return data['data']
    return None

def calculate_density_altitude(elevation_ft, temperature_c, altimeter_hpa):
    # Convert altimeter setting to pressure altitude (assuming altimeter is set to 29.92 inHg)
    altimeter_inHg = altimeter_hpa * 0.02953
    pressure_altitude = (29.92 - altimeter_inHg) * 1000 + elevation_ft
    
    # Calculate ISA temperature at the given elevation (in °C)
    isa_temperature = 15 - (2 * (elevation_ft / 1000))
    
    # Calculate Density Altitude using the FAA formula
    density_altitude = pressure_altitude + (120 * (temperature_c - isa_temperature))
    
    return density_altitude


# Parse METAR data into fields for InfluxDB
def parse_metar_data(metar_data):
    elevation = metar_data['elevation']['feet'] if 'elevation' in metar_data else None
    temperature = metar_data['temperature']['celsius'] if 'temperature' in metar_data else None
    altimeter = metar_data['barometer']['mb'] if 'barometer' in metar_data else None

    density_altitude = None
    if elevation is not None and temperature is not None and altimeter is not None:
        density_altitude = calculate_density_altitude(elevation, temperature, altimeter)
    
    parsed_data = {
        "airport": metar_data.get('icao', ''),
        "temperature": temperature,
        "dewpoint": metar_data['dewpoint']['celsius'] if 'dewpoint' in metar_data else None,
        "wind_speed": metar_data['wind']['speed_kts'] if 'wind' in metar_data else None,
        "wind_gust": metar_data['wind']['gust_kts'] if 'wind' in metar_data and 'gust_kts' in metar_data['wind'] else None,
        "wind_direction": metar_data['wind']['degrees'] if 'wind' in metar_data else None,
        "visibility": metar_data['visibility']['meters'] if 'visibility' in metar_data else None,
        "altimeter": altimeter,
        "elevation": elevation,
        "density_altitude": density_altitude
    }
    return parsed_data

# Prepare the data for InfluxDB
def prepare_influxdb_payload(parsed_data):
    fields = []
    for key, value in parsed_data.items():
        if value is not None and key != "airport":
            if isinstance(value, str):
                fields.append(f'{key}="{value}"')
            else:
                fields.append(f'{key}={value}')
    field_str = ','.join(fields)
    timestamp = int(time.time())
    data = f"metar,airport={parsed_data['airport']} {field_str} {timestamp}"
    return data

# Send data to InfluxDB
def send_to_influxdb(payload):
    headers = {
        'Authorization': f'Token {INFLUXDB_API_KEY}',
        'Content-Type': 'text/plain'
    }
    response = requests.post(INFLUXDB_URL, headers=headers, data=payload)
    if response.status_code == 204:
        print(f"Successfully sent data to InfluxDB for airport {payload.split(',')[1].split('=')[1]}")
    else:
        print(f"Failed to send data to InfluxDB: {response.status_code}, {response.text}")

# Main processing
while True:
    metar_data_list = fetch_metar_data(AIRPORTS)
    if metar_data_list:
        for metar_info in metar_data_list:
            parsed_data = parse_metar_data(metar_info)
            influxdb_payload = prepare_influxdb_payload(parsed_data)
            send_to_influxdb(influxdb_payload)
    else:
        print("Could not fetch data for the airports")
    
    print(f"Sleeping for {INTERVAL} seconds...")
    time.sleep(INTERVAL)
