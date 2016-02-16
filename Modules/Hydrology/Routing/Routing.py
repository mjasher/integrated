from __future__ import division
import pandas as pd
import numpy as np

import time

from integrated.Modules.Core.IntegratedModelComponent import Component
from integrated.Modules.Core.Handlers.FileHandler import FileHandler

class Routing(Component):

    def __init__(self, Climate, water_volume):
        """
        comment
        """

        self.Climate = Climate 
        self.water_volume = water_volume
        self.water_volume.index = water_volume["node"]

        self.runtime = 0.0
    #End init()

    # def run(self):

    #     pass
    # #End run()

    def calcFlow(self, node_id, climate, node_inflow, irrig_ext, local_inflow, base_flow, deep_drainage, Routingparams):

        """
        :math:`g = f * d`

        :sup:`a`:math:`E_{k}` if :math:`M_{k} < g`

        :math:`eE_{k}e^-2(M_{k}-g)` if :math:`M_{k} > g`

        """

        t = time.time()

        evap, rain = climate

        Gamma_k = base_flow - deep_drainage #These could come from external module
        
        # storage_coef, ET_f, area = Routingparams
        storage_coef=0.1; ET_f=1.2; area=0.1;

        #Fastest data extraction method so far
        bore_id, n_id, water_volume = self.water_volume.loc[node_id]

        # tmp_vol = water_info["water_volume"] + (node_inflow + local_inflow + Gamma_k) +(rain - evap*ET_f)*area - irrig_ext
        tmp_vol = water_volume + (node_inflow + local_inflow + Gamma_k) + (rain - evap*ET_f)*area - irrig_ext

        if tmp_vol > 0:
            water_volume = 1/(1+storage_coef) * tmp_vol
            outflow=storage_coef*water_volume
        else:
            water_volume = tmp_vol
            outflow=0.0

        # water_info = self.water_volume[self.water_volume['node'] == node_id].iloc[0]
        # print water_info

        # tmp = water_info["water_volume"] + (node_inflow + local_inflow + Gamma_k) +(rain - evap*ET_f)*area - irrig_ext
        # if tmp >0:
        #     water_volume = 1/(1+storage_coef) * tmp
        #     outflow=storage_coef*water_volume
        # else:
        #     water_volume = tmp
        #     outflow=0.0

        self.runtime += time.time() - t

        return outflow, water_volume

    #End calcFlow()
