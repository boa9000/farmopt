import logging
import numpy as np


logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(message)s"
)


class SimulatedAnnealer:
    def __init__(self, iterations, verbose = True):
        self.T = 1
        self.T_final = 1e-2
        self.iterations = iterations
        self.cooling = (self.T_final / self.T) ** (1 / self.iterations)
        self.min_LCOE = 50.0
        self.min_LCOE_hist = []
        self.min_LCOE_alloc = []
        self.max_AEP = 0
        self.max_AEP_hist = []
        self.max_AEP_alloc = []
        self.current_LCOE = 50.0
        self.prev_LCOE = 50.0
        self.delta_list = []
        self.lcoe_hist = []
        self.aep_hist = []
        self.aep_at_min_lcoe = 0


        self.verbose = verbose

    def check_LCOE(self, lcoe, allocations, aep):
        self.lcoe_hist.append(lcoe)
        if lcoe < self.min_LCOE:
            self.min_LCOE = lcoe
            self.min_LCOE_hist.append(self.min_LCOE)
            self.min_LCOE_alloc = allocations
            self.aep_at_min_lcoe = aep
            if self.verbose:
                logging.info(f"New min_LCOE: {self.min_LCOE}")
        self.check_AEP(aep,allocations)


    def check_AEP(self, aep, allocations):
        self.aep_hist.append(aep)
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





        
        