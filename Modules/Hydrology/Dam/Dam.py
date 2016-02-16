from __future__ import division
import pandas as pd
import numpy as np
from integrated.Modules.Core.IntegratedModelComponent import Component
from integrated.Modules.Core.Handlers.FileHandler import FileHandler

class Dam(Component):
    def __init__(self, Climate, water_volume):
        """
        comment
        """

        self.Climate = Climate 
        self.water_volume = water_volume

    def run(self):

        pass
    #End init()

    def calcFlow(self, node_id, climate, node_inflow, irrig_ext, base_flow, deep_drainage, Damparams):

        """
        :math:`g = f * d`

        :sup:`a`:math:`E_{k}` if :math:`M_{k} < g`

        :math:`eE_{k}e^-2(M_{k}-g)` if :math:`M_{k} > g`

        """

        evap, rain = climate

        Gamma_k = base_flow - deep_drainage
        
        storage_coef, area, max_storage = Damparams

        #Fastest data extraction method so far
        gauge_id, n_id, water_volume = self.water_volume.loc[node_id]

        # print(node_id,gauge_id,n_id,water_volume)  
        # print(self.water_volume)
        
        tmp_vol = water_volume + (node_inflow + Gamma_k) + (rain - evap)*area - irrig_ext

        if tmp_vol > max_storage:
            water_volume = 1/(1+storage_coef) * (tmp_vol-max_storage)
            outflow=storage_coef*(water_volume)
            water_volume = water_volume + max_storage
        else:
            water_volume = tmp_vol
            outflow=0.0

        return outflow, water_volume

    #End calcFlow()
    
#End Dam
