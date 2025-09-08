import farmopt.data_retriever as dr
import numpy as np
from floris import (
    FlorisModel,
    TimeSeries,
    WindRose,
)


class DataManipulator:
    def __init__(self, weather_retriever: dr.WeatherRetriever):
        self.wather_retriever = weather_retriever
        self.weather = weather_retriever.weather
        self.reference_height = 100  
        self.target_height = 90      
        self.alpha = 0.12             
        self.turbulence_intensity = 0.06 
        self.wr = None

    def wind_rose(self, year = 2023):
        """
        generate a wind rose from the weather data.
        
        Parameters:
        df (pd.DataFrame): A DataFrame containing the weather data.

        Returns:
        WindRose: A WindRose object.
        """
        if not self.weather:
            self.wather_retriever.retrieve_weather(year)
        
        reference_height = self.reference_height
        target_height = self.target_height
        alpha = self.alpha
        df = self.weather.copy()
        df["wind_speed_100m"] = df["wind_speed_100m"] * (target_height / reference_height) ** alpha
        df["ws"] = (df["wind_speed_100m"] *2).round() /2
        df["wd"] = (df["wind_direction_100m"] / 30).round() * 30
        df["wd"].replace(360, 0, inplace = True)
        
        dff = df.groupby(['ws', 'wd']).value_counts().reset_index()
        dff['freq_val'] = dff['count']/dff['count'].sum()
        dff.drop('count', axis = 1, inplace=True)

        wd = dff['wd'].values
        ws = dff['ws'].values
        freq = dff['freq_val'].values

        unique_wd = np.unique(wd)
        unique_ws = np.unique(ws)

        wd_step = unique_wd[1] - unique_wd[0]
        ws_step = unique_ws[1] - unique_ws[0]

        time_series = TimeSeries(wd, ws, self.turbulence_intensity)

        self.wr = time_series.to_WindRose(wd_step=wd_step, ws_step=ws_step, bin_weights=freq)
        
        return self.wr
        
    def plot_wind_rose(self):
        if not self.wr:
            raise ValueError("Wind rose not generated yet. Call wind_rose() first.")
        
        self.wr.plot()

    