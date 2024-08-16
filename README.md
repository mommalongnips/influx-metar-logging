# METAR Data Fetcher

## Overview

The METAR Data Fetcher is a Python-based application designed to fetch METAR (Meteorological Aerodrome Report) data for specified airports. It calculates the density altitude based on the fetched METAR data and stores the information in an InfluxDB database. The application is designed to run as a Docker container and can be configured entirely via environment variables.

## Features

- Fetches METAR data from the CheckWX API for one or more airports.
- Calculates the density altitude using METAR data.
- Stores the METAR data and calculated density altitude in an InfluxDB instance.
- Fully configurable through environment variables.

## Prerequisites

- Docker and Docker Compose installed on your machine.
- A CheckWX API key.
- An InfluxDB instance with an API key.
- Python 3.x installed (if running locally without Docker).

## Environment Variables

The application is configured through the following environment variables:

| Variable          | Description                                                  | Default            | Required |
| ----------------- | ------------------------------------------------------------ | ------------------ | -------- |
| `CHECKWX_API_KEY` | Your CheckWX API key. This is required to fetch METAR data.  |                    | Yes      |
| `INFLUXDB_API_KEY`| Your InfluxDB API key. Used to authenticate with your InfluxDB instance. |                    | Yes      |
| `INFLUXDB_HOST`   | The hostname or IP address of your InfluxDB instance.         |                    | Yes      |
| `INFLUXDB_PORT`   | The port on which InfluxDB is running.                        | `8086`             | Yes      |
| `INFLUXDB_BUCKET` | The name of your InfluxDB bucket where data will be stored.   |                    | Yes      |
| `INFLUXDB_ORG`    | The name of your InfluxDB organization.                       |                    | Yes      |
| `AIRPORTS`        | Comma-separated list of airport ICAO codes to fetch METAR data for. | `KBJC,KFNL`        | No       |
| `INTERVAL`        | The interval (in seconds) between data fetches. A warning is issued if set to less than 60 seconds. | `60`               | No       |
