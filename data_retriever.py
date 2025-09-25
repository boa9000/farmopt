import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
from ipyleaflet import Map, DrawControl
from ipyleaflet import Polygon as LeafletPolygon
from shapely.geometry import Polygon, MultiPolygon
import utils



class WeatherRetriever:
    def __init__(self, default = False):
        self.coordinates = None
        self.constraints = None
        self.centroid = None
        self.weather = None

        if default:
            self.coordinates = [[[15.07925, 52.222121],
                                [15.054703, 52.232531],
                                [15.068092, 52.238523],
                                [15.059166, 52.251977],
                                [15.095215, 52.25597],
                                [15.130234, 52.251556],
                                [15.133324, 52.244515],
                                [15.124397, 52.225486],
                                [15.092468, 52.21823],
                                [15.07925, 52.222121]],
                                [[15.070152, 52.216652],
                                [15.057449, 52.223383],
                                [15.067062, 52.223383],
                                [15.074272, 52.218335],
                                [15.070152, 52.216652]],
                                [[15.066719, 52.257231],
                                [15.090408, 52.263115],
                                [15.128174, 52.262064],
                                [15.136757, 52.259542],
                                [15.135384, 52.257021],
                                [15.122337, 52.254288],
                                [15.066719, 52.257231]]]
            self.constraints = [[[15.101051, 52.245881],
                                [15.094185, 52.237892],
                                [15.103798, 52.233267],
                                [15.114441, 52.235159],
                                [15.120964, 52.23621],
                                [15.121994, 52.243358],
                                [15.101051, 52.245881]],
                                [[15.091782, 52.253238],
                                [15.103798, 52.258912],
                                [15.102081, 52.251346],
                                [15.097618, 52.248193],
                                [15.091782, 52.253238]],
                                [[15.087662, 52.223173],
                                [15.057793, 52.230113],
                                [15.058479, 52.233898],
                                [15.075302, 52.236421],
                                [15.096245, 52.238103],
                                [15.098991, 52.226538],
                                [15.087662, 52.223173]],
                                [[15.052643, 52.243358],
                                [15.095901, 52.268367],
                                [15.067062, 52.245461],
                                [15.052643, 52.243358]]]
            self.calculate_centroid()
                                        

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
                "fillOpacity": 0.2,
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
        # elif len(self.coordinates) > 1:
        #     raise ValueError(f"Please draw just one polygon. {len(self.coordinates)} polygons detected.")
        else:
            polygons = [Polygon(coords) for coords in self.coordinates]
            multi = MultiPolygon(polygons) 
            centroid = multi.centroid
            self.centroid = (centroid.y, centroid.x)
            self.best_epsg = utils.best_epsg(centroid)
            self.country = utils.country_finder(centroid)

    def set_constraints(self):
        if self.coordinates is None:
            raise ValueError("No coordinates available. Please draw a polygon first.")
        elif self.centroid is None:
            self.calculate_centroid() 
        
        m = Map(center = self.centroid, zoom = 12)
        draw_control = DrawControl(circle = {}, circlemarker = {}, marker = {}, polyline = {})
        draw_control.polygon = {
            "shapeOptions": {
                "color": "#81125c",
                "weight": 4,
                "opacity": 1.0,
                "fillOpacity": 0.4,
            },
            "drawError": {
                "color": "#dd253b",
                "message": "Oups! You can't draw that!",
            },
            "allowIntersection": False,
        }
        m.add_control(draw_control)

        polygon_coords = self.flip_coordinates(self.coordinates)
        polygon = LeafletPolygon(
            locations=polygon_coords,
            color="blue",  
            fill_color="blue",
            fill_opacity=0.2,
            weight=4
        )
        m.add(polygon)

        constraints = []

        def handle_draw(target, action, geo_json):
            if action == "created":
                constraints.append(geo_json["geometry"]["coordinates"][0])
            if action == "deleted":
                constraints.remove(geo_json["geometry"]["coordinates"][0])
        
        draw_control.on_draw(handle_draw)
        self.constraints = constraints
        return m
    
    def flip_coordinates(self, coords):
        polygons = []
        for i in range(len(coords)):
            polygon_coords = [tuple(coord[::-1]) for coord in coords[i]]
            polygons.append(polygon_coords)
            
        return polygons