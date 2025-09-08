import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
from ipyleaflet import Map, DrawControl
from shapely.geometry import Polygon



class WeatherRetriever:
    def __init__(self):
        self.coordinates = None
        self.centroid = None
        self.weather = None
        self.reference_height = 100  # meters (current data height)
        self.target_height = 90      # meters (desired height, change as needed)
        self.alpha = 0.12             # wind shear exponent

    def retrieve_weather(self, year = 2023):
        """
        Retrieve weather data for the given longitude and latitude.

        Parameters:
        longitude (float): The longitude of the location.
        latitude (float): The latitude of the location.

        Returns:
        pd.DataFrame: A DataFrame containing the weather data.
        """
        if not self.centroid:
            self.calculate_centroid()

        # Setup the Open-Meteo API client with cache and retry on error
        cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
        retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
        openmeteo = openmeteo_requests.Client(session = retry_session)

        # Make sure all required weather variables are listed here
        # The order of variables in hourly or daily is important to assign them correctly below
        url = "https://archive-api.open-meteo.com/v1/archive"

        params = {
            "latitude": self.centroid[0],
            "longitude": self.centroid[1],
            "start_date": f"{year}-01-01",
            "end_date": f"{year}-12-31",
            "hourly": ["temperature_2m", "wind_direction_100m", "wind_speed_100m"],
        }
        responses = openmeteo.weather_api(url, params=params)

        # Process first location. Add a for-loop for multiple locations or weather models
        response = responses[0]
        print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
        print(f"Elevation: {response.Elevation()} m asl")
        print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")

        # Process hourly data. The order of variables needs to be the same as requested.
        hourly = response.Hourly()
        hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
        hourly_wind_direction_100m = hourly.Variables(1).ValuesAsNumpy()
        hourly_wind_speed_100m = hourly.Variables(2).ValuesAsNumpy()

        hourly_data = {"date": pd.date_range(
            start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
            end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
            freq = pd.Timedelta(seconds = hourly.Interval()),
            inclusive = "left"
        )}

        hourly_data["temperature_2m"] = hourly_temperature_2m
        hourly_data["wind_speed_100m"] = hourly_wind_speed_100m
        hourly_data["wind_direction_100m"] = hourly_wind_direction_100m


        self.weather = pd.DataFrame(data = hourly_data)

        return self.weather
    
    def get_coordinates(self):
        """
        get coordinates by drawing a polygon on a map.
        
        """
        m = Map(center = (52.52, 13.405), zoom = 8)

        draw_control = DrawControl(circle = {}, circlemarker = {}, marker = {}, polyline = {})
        draw_control.polygon = {
            "shapeOptions": {
                "color": "#6bc2e5",
                "weight": 4,
                "opacity": 1.0,
                "fillOpacity": 0.5,
            },
            "drawError": {
                "color": "#dd253b",
                "message": "Oups! You can't draw that!",
            },
            "allowIntersection": False,
        }

        m.add_control(draw_control)
        coordinates = []

        def handle_draw(target, action, geo_json):
            if action == "created":
                coordinates.append(geo_json["geometry"]["coordinates"][0])
            if action == "deleted":
                coordinates.remove(geo_json["geometry"]["coordinates"][0])
        
        draw_control.on_draw(handle_draw)
        self.coordinates = coordinates
        return m
    
    def calculate_centroid(self):
        """
        calculate the centroid of the drawn polygon.
        
        """
        if not self.coordinates:
            raise ValueError("No coordinates available. Please draw a polygon first.")
        elif len(self.coordinates) > 1:
            raise ValueError(f"Please draw just one polyogon. {len(self.coordinates)} polygons detected.")
        else:
            polygon = Polygon(self.coordinates[0])
            centroid = polygon.centroid
            self.centroid = (centroid.y, centroid.x)

