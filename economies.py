import yaml
import pandas as pd

class Econom:
    def __init__(self):
        with open("config.yml", "r") as f:
            config = yaml.safe_load(f)

        self.r = config.get("discount_rate")
        self.N = config.get("project_lifetime")
        self.energy_price = None

        self.no_of_turbines = config.get("number_of_turbines")
        self.turbine_cost = config.get("turbine_cost_per_mw")
        self.turbine_opex = config.get("operation_cost_per_mw")
        
        self.lease = config.get("lease")
        self.land_cost = config.get("land_cost_per_m2")
        self.lease_cost = config.get("land_lease_per_m2")

        self.cable_cost = config.get("price_of_cable_per_m")
        self.substation_cost = config.get("price_of_substation")
        self.permitting_cost = config.get("permitting_cost_percent")
        self.other_costs = config.get("other_costs")

        self.crf = (self.r * (1 + self.r) ** self.N) / ((1 + self.r) ** self.N - 1)
        
        self.land_lease_prices = pd.read_csv("data/land_lease_price.csv")
        self.land_purchase_prices = pd.read_csv("data/land_purchase_price.csv")

    def calculate_capex(self, cable_length):
        capex = 0
        turbines_cost = self.no_of_turbines * self.turbine_cost
        other_costs = self.other_costs * turbines_cost
        cables_cost = cable_length*self.cable_cost
        opex = turbines_cost * self.turbine_opex
        if self.lease:
            opex += self.lease_cost
        else:
            capex += self.land_cost

        capex += turbines_cost + other_costs + cables_cost
        self.capex = capex
        self.opex = opex


    def get_lcoe(self, aep, cable_length):
        self.calculate_capex(cable_length)
        return ((self.capex * self.crf + (self.opex)) / aep) * 1000 # because aep is in Wh, to change to kWh
        
    