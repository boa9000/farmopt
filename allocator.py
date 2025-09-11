import geopandas as gpd
import data_retriever as dr
import modeling as mdl
from shapely.geometry import Polygon, MultiPolygon, Point
import numpy as np
from ipyleaflet import Map, CircleMarker, LayerGroup,GeoJSON
import time
import json

class Allocator:
    def __init__(self, data_retriever: dr.WeatherRetriever, fm: mdl.FarmModel):
        self.data_retriever = data_retriever
        self.coordinates = data_retriever.coordinates
        self.constraints = data_retriever.constraints
        self.centroid = data_retriever.centroid
        self.no_of_turbines = fm.no_of_turbines
        self.bounds = []
        self.available_gdf = None
        self.allocations = None
        self.m = None

        self.intitial_allocation()

    def intitial_allocation(self):
        if self.coordinates is None:
            raise ValueError("No coordinates available. Please draw a polygon first.")
        elif self.centroid is None:
            self.data_retriever.calculate_centroid()
            self.centroid = self.data_retriever.centroid
        
        constraints_polygons = [Polygon([tuple(pt) for pt in poly]) for poly in self.constraints]
        gdf_constraints = gpd.GeoDataFrame({'geometry': constraints_polygons}, crs="EPSG:4326")

        coord_polygons = [Polygon([tuple(pt) for pt in poly]) for poly in self.coordinates]
        gdf_coord = gpd.GeoDataFrame({'geometry': coord_polygons}, crs="EPSG:4326")

        self.available_gdf = gpd.overlay(gdf_coord, gdf_constraints, how="difference").to_crs("EPSG=3035")

        minx = self.available_gdf.bounds.minx
        miny = self.available_gdf.bounds.miny
        maxx = self.available_gdf.bounds.maxx
        maxy = self.available_gdf.bounds.maxy
        self.bounds = [minx, miny, maxx, maxy]
        allocations = []
        
        # generate more points than needed, filter inside polygon
        while len(allocations) < self.no_of_turbines:
            x = np.random.uniform(minx, maxx, self.no_of_turbines*2)
            y = np.random.uniform(miny, maxy, self.no_of_turbines*2)
            candidates = [Point(xi, yi) for xi, yi in zip(x, y)]
            allocations.extend([p for p in candidates if self.available_gdf.contains(p).values[0]])
            allocations = allocations[:self.no_of_turbines]  # keep only n_points
        
        self.allocations = allocations


    
    def allocate_turbine(self, R = 1):
        minx, miny, maxx, maxy = self.bounds
        x = np.random.uniform(minx, maxx)
        y = np.random.uniform(miny, maxy)
        p = Point(x, y)

        while not self.available_gdf.contains(p).values[0]:
            x = np.random.uniform(minx, maxx)
            y = np.random.uniform(miny, maxy)
            p = Point(x, y)
        
        return p

    def mapper(self):
        if self.allocations is None:
            raise RuntimeError("Cannot run this before allocations are initialized")
        
        self.m = Map(center=self.centroid, zoom=10)
        self.points_layer = LayerGroup()
        self.m.add_layer(self.points_layer)

        self.update_points()

        geo_json_data = json.loads(self.available_gdf.to_json())
        geo_json_layer = GeoJSON(data=geo_json_data, style={
            "color": "blue",
            "opacity": 1,
            "fillColor": "blue",
            "fillOpacity": 0.3
        })
        self.m.add_layer(geo_json_layer)

        return self.m


    def start(self):
        if self.m is None:
            raise RuntimeError("Run mapper() first.")
        for i in range(500):
            idx = np.random.randint(len(self.allocations))
            self.allocations[idx] = self.allocate_turbine()
            self.update_points()
            time.sleep(0.01) 



    def update_points(self):
        # Clear previous points
        self.points_layer.clear_layers()
        
        # Add current points
        for point in self.allocations:
            lat, lon = point.y, point.x  # ipyleaflet expects (lat, lon)
            marker = CircleMarker(location=(lat, lon), radius=2, color="red", fill_color="red")
            self.points_layer.add_layer(marker)