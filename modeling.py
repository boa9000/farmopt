import data_retriever as dr
import numpy as np
from floris import (
    FlorisModel,
    TimeSeries,
    WindRose,
)
import pandas as pd
import yaml
import logging


logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(message)s"
)

class ModelData:
    def __init__(self, weather_retriever: dr.WeatherRetriever):
        self.weather_retriever = weather_retriever
        self.weather = weather_retriever.weather
        self.wr = None

        with open("config.yml", "r") as f:
            config = yaml.safe_load(f)

        self.no_of_turbines = config.get("number_of_turbines")
        self.turbulence_intensity = config.get("turbulence_intensity")
        self.reference_height = config.get("reference_height", 100)
        self.target_height = config.get("target_height")
        self.alpha = config.get("wind_shear")
        self.ws_resolution = config.get("wind_speed_resolution")
        self.wd_resolution = config.get("wind_direction_resolution")

        self.wind_rose()

    def wind_rose(self, year = 2023):
        """
        generate a wind rose from the weather data.
        
        Parameters:
        df (pd.DataFrame): A DataFrame containing the weather data.

        Returns:
        WindRose: A WindRose object.
        """
        if self.weather is None:
            self.weather_retriever.retrieve_weather(year)
            self.weather = self.weather_retriever.weather
        
        df = self.weather.copy()
        df["wind_speed_100m"] = df["wind_speed_100m"].clip(upper=30)
        df["wind_speed_100m"] = df["wind_speed_100m"] * (self.target_height / self.reference_height) ** self.alpha
        df["ws"] = (df["wind_speed_100m"] / self.ws_resolution).round() * self.ws_resolution
        df["wd"] = (df["wind_direction_100m"] / self.wd_resolution).round() * self.wd_resolution
        df["wd"].replace(360, 0, inplace = True)
        dff = df[['ws', 'wd']]
        dff = dff.groupby(['ws', 'wd']).value_counts().reset_index()
        dff['freq_val'] = dff['count']/dff['count'].sum()
        dff.drop('count', axis = 1, inplace=True)
        self.frequency_df = dff
        

        # sum all the freq ov over 30 and add them to 30 (or last entry, more robust)
        # extra = dff.loc[df["ws"] > 30].groupby("wd")["freq_val"].sum()
        # dff = dff[dff["ws"] <= 30]
        # dff.loc[dff.index[-1], "freq_val"] += extra
        # set all ws above 30 as 30 in the weather file from the beginning

        self.dff = dff # for debugging

        wd = dff['wd'].values
        ws = dff['ws'].values
        freq = dff['freq_val'].values

        unique_wd = np.unique(wd)
        unique_ws = np.unique(ws)

        wd_step = unique_wd[1] - unique_wd[0]
        ws_step = unique_ws[1] - unique_ws[0]

        time_series = TimeSeries(wd, ws, self.turbulence_intensity)

        self.wr = time_series.to_WindRose(wd_step=wd_step, ws_step=ws_step, bin_weights=freq)
        
        self.plot_wind_rose()
        
    def plot_wind_rose(self):
        if not self.wr:
            raise ValueError("Wind rose not generated yet. Call wind_rose() first.")
        
        self.wr.plot()


class FarmModel:
    def __init__(self, data_manipulator: ModelData = None):
        self.data_manipulator = data_manipulator
        self.wr = data_manipulator.wr
        self.floris = None

        with open("config.yml", "r") as f:
            config = yaml.safe_load(f)

        self.model_file = config.get("floris_model_file")
        self.no_of_turbines = config.get("number_of_turbines")

        self.setup_floris()

    def setup_floris(self):
        if not self.wr:
            raise ValueError("Wind rose not generated yet. run setup_floris() after getting wind rose.")

        self.floris = FlorisModel(self.model_file)
        self.floris.set(wind_data = self.wr)

        floris_logger = logging.getLogger("floris.floris_model.FlorisModel")
        floris_logger.setLevel(logging.ERROR)

    
    def new_run(self, positions):
        xs = [p.x for p in positions]
        ys = [p.y for p in positions]
        self.floris.set(layout_x = xs, layout_y= ys)
        self.floris.run()


    def get_aep(self):
        return self.floris.get_farm_AEP()

