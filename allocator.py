import geopandas as gpd
import data_retriever as dr
import modeling as mdl
from shapely.geometry import Polygon, MultiPolygon, Point
import numpy as np
from ipyleaflet import Map, CircleMarker, LayerGroup,GeoJSON
import time
import json
import utils
import economies
import simulated_annealing
from scipy.spatial.distance import pdist, squareform
from scipy.sparse.csgraph import minimum_spanning_tree
from pyproj import Transformer
import yaml


class Allocator:
    def __init__(self, data_retriever: dr.WeatherRetriever, fm: mdl.FarmModel):
        self.data_retriever = data_retriever
        self.coordinates = data_retriever.coordinates
        self.constraints = data_retriever.constraints
        self.centroid = data_retriever.centroid
        self.best_epsg = data_retriever.best_epsg
        self.country = data_retriever.country
        self.no_of_turbines = fm.no_of_turbines
        self.fm = fm
        self.bounds = []
        self.available_gdf = None
        self.current_allocations = None
        self.prev_allocations = None
        self.m = None
        self.transformer = Transformer.from_crs(self.best_epsg, "EPSG:4326", always_xy=True)
        

        with open("config.yml", "r") as f:
            config = yaml.safe_load(f)
        
        self.iterations = config.get("iterations")
        self.intitial_allocation()

        self.R0 = np.sqrt(self.area) 
        self.R = self.R0

        self.econ = economies.Econom(self.country, self.area)
        self.sa = simulated_annealing.SimulatedAnnealer(self.iterations)


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
        self.area = gdf_coord.to_crs(epsg=self.best_epsg).geometry.area.sum()


        self.available_gdf = gpd.overlay(gdf_coord, gdf_constraints, how="difference").to_crs(epsg=self.best_epsg)
        self.area_cut = self.available_gdf.geometry.area.sum()

        minx, miny, maxx, maxy = self.available_gdf.total_bounds
        self.bounds = self.available_gdf.total_bounds
        allocations = []
        
        # generate more points than needed, filter inside polygon
        while len(allocations) < self.no_of_turbines:
            x = np.random.uniform(minx, maxx, self.no_of_turbines*2)
            y = np.random.uniform(miny, maxy, self.no_of_turbines*2)
            candidates = [Point(xi, yi) for xi, yi in zip(x, y)]
            allocations.extend([p for p in candidates if self.available_gdf.contains(p).values[0]])
            allocations = allocations[:self.no_of_turbines]  # keep only n_points
        
        self.current_allocations = allocations
        self.prev_allocations = self.current_allocations


    
    def allocate_turbine_absolute(self):
        minx, miny, maxx, maxy = self.bounds
        x = np.random.uniform(minx, maxx)
        y = np.random.uniform(miny, maxy)
        p = Point(x, y)

        while not self.available_gdf.contains(p).values.any():
            x = np.random.uniform(minx, maxx)
            y = np.random.uniform(miny, maxy)
            p = Point(x, y)
        
        return p
    
    def allocate_turbine(self, pos):
        x = np.random.uniform(pos.x-self.R, pos.x+self.R)
        y = np.random.uniform(pos.y-self.R, pos.y+self.R)
        p = Point(x, y)

        while not self.available_gdf.contains(p).values.any():
            x = np.random.uniform(pos.x-self.R, pos.x+self.R)
            y = np.random.uniform(pos.y-self.R, pos.y+self.R)
            p = Point(x, y)
        
        return p
        

    def obtain_new_positions(self, i):
       p = self.allocate_turbine(self.current_allocations[i])
       self.current_allocations[i] = p


    def run(self):
        for iteration in range(self.iterations):
            for i in range(len(self.current_allocations)):
                self.obtain_new_positions(i)
                self.fm.new_run(self.current_allocations)  # run Fmodel
                aep = self.fm.get_aep()  # obtain aep
                cables_length,subs = self.get_cables_length_and_substation()
                lcoe = self.econ.get_lcoe(aep,cables_length)   # obtain lcoe  
                self.sa.check_LCOE(lcoe, self.current_allocations, aep)  # check lcoe # check aep with lcoe
                acceptance = self.sa.annealing_acceptance(lcoe)  # check annealingacc
                if acceptance:  # change pos or not
                    self.prev_allocations = self.current_allocations
                    self.update_points() # update map
                    print("accepted")
                else:
                    self.current_allocations = self.prev_allocations
                self.sa.update()
            self.R = max(self.R0*0.1, self.R0 * (1 - iteration / self.iterations))



    def mapper(self):
        if self.current_allocations is None:
            raise RuntimeError("Cannot run this before allocations are initialized")
        
        self.m = Map(center=self.centroid, zoom=10)
        self.points_layer = LayerGroup()
        self.m.add_layer(self.points_layer)

        self.update_points()

        geo_json_data = json.loads(self.available_gdf.to_crs(epsg=4326).to_json())
        geo_json_layer = GeoJSON(data=geo_json_data, style={
            "color": "blue",
            "opacity": 1,
            "fillColor": "blue",
            "fillOpacity": 0.3
        })
        self.m.add_layer(geo_json_layer)

        return self.m



    def update_points(self):
        # Clear previous points
        self.points_layer.clear_layers()
        points = self.transform_points()
        # Add current points
        for point in points:
            lat, lon = point.y, point.x  # ipyleaflet expects (lat, lon)
            marker = CircleMarker(location=(lat, lon), radius=2, color="red", fill_color="red")
            self.points_layer.add_layer(marker)


    def transform_points(self):
        points_epsg4326 = []
        for pt in self.current_allocations:
            lon, lat = self.transformer.transform(pt.x, pt.y)
            points_epsg4326.append(Point(lon, lat))
        return points_epsg4326



    def get_cables_length_and_substation(self):
        coords = np.array([[p.x, p.y] for p in self.current_allocations])
        dist_matrix = squareform(pdist(coords))  
        mst = minimum_spanning_tree(dist_matrix)
        centroid = np.mean(coords, axis=0)
        substation = Point(centroid[0], centroid[1])
        return mst.sum(), substation

    def show_best_lcoe(self):
        self.current_allocations = self.sa.min_LCOE_alloc
        self.update_points()
        print(f"Best LCOE is {self.sa.min_LCOE:.2f} ct/kWh")