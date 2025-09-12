import logging
import numpy as np


logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(message)s"
)


class SimulatedAnnealer:
    def __init__(self, verbose = True):
        self.T = 0.5
        self.cooling = 0.99
        self.R = 1000
        self.max_iter = 5000
        self.min_LCOE = 2.0
        self.min_LCOE_hist = []
        self.min_LCOE_alloc = []
        self.max_AEP = 0
        self.max_AEP_hist = []
        self.max_AEP_alloc = []
        self.current_LCOE = 2.0
        self.prev_LCOE = 2.0
        self.delta_list = []


        self.verbose = verbose

    def check_LCOE(self, lcoe, allocations):
        if lcoe < self.min_LCOE:
            self.min_LCOE = lcoe
            self.min_LCOE_hist.append(self.min_LCOE)
            self.min_LCOE_alloc = allocations
            if self.verbose:
                logging.info(f"New min_LCOE: {self.min_LCOE}")

    def check_AEP(self, aep, allocations):
        if aep > self.max_AEP:
            self.max_AEP = aep
            self.max_AEP_hist.append(self.max_AEP)
            self.max_AEP_alloc = allocations
            if self.verbose:
                logging.info(f"New max_AEP: {self.max_AEP}")


    def annealing_acceptance(self, lcoe):
        delta = lcoe - self.prev_LCOE
        self.delta_list.append(delta)
        if delta <= 0.0:
            self.prev_LCOE = lcoe
            return True
        elif delta > 0.0:
            u = np.random.uniform()
            if u < np.exp(- (delta) / self.T):
                self.prev_LCOE = lcoe
                return True
        else:
            return False

    def update(self):
        self.T *= self.cooling





        
        