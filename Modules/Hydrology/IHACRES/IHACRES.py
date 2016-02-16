from __future__ import division

from integrated.Modules.Core.IntegratedModelComponent import Component
from integrated.Modules.Core.Handlers.FileHandler import FileHandler

import pandas as pd
import numpy as np

import time


class IHACRES(Component):
    def __init__(self, Climate, water_deficit, params):
        """
        comment
        """

        self.Climate = Climate 
        self.water_deficit = water_deficit
        self.params = params

        #Reset index to node numbers
        self.params.index = self.params["node"]

        self.prep_time = 0.0
        self.calc_time = 0.0
        self.get_climate = 0.0
        self.get_params = 0.0
    #End init()

    def calcCMD(self, node_id, climate, CMD_old, Sflow_old): 
    #d1z, d2z, ez, fz, alphaz, areaz, az):

        """
        :math:`g = f * d`

        :sup:`a`:math:`E_{k}` if :math:`M_{k} < g`

        :math:`eE_{k}e^-2(M_{k}-g)` if :math:`M_{k} > g`

        """

        prep_start = time.time()

        climate_vars = time.time()
        evap, rain = climate
        #print(node_id,evap,rain)
        self.get_climate += time.time() - climate_vars

        get_params = time.time()
        #Turns out in this context its much quicker to grab all the values and throw away the ones we don't need
        # i, n, d1, d2, e, f, alpha, area, a = self.params.loc[self.params["node"] == node_id].iloc[0]
        i, n, d1, d2, e, f, alpha, area, a = self.params.loc[node_id]
        #	print(node_id,area,rain,evap,CMD_old,Sflow_old)

        self.get_params += time.time() - get_params

        self.prep_time += time.time() - prep_start

        calc_time = time.time()

        cmd2 = CMD_old
        if cmd2 > d2+rain:
            cmd = cmd2-rain
            u = 0.0
            r = 0.0
        else:
            if cmd2 > d2:
                rain2 = rain-(cmd2-d2)
                cmd2 = d2
            else:
                rain2 = rain

            epsilonn = d2/(1.0-alpha)
            rain3 = epsilonn * np.log((alpha+cmd2/epsilonn)/(alpha+d1/epsilonn))
            if rain3 >= rain2: #cmd2 > m:
                lamda = np.exp(rain2*(1.0-alpha)/d2)
                epsilon = alpha*epsilonn
                cmd = cmd2/lamda-epsilon*(1.0-1.0/lamda)
                u = 0.0
                #r = rain-(CMD_old-cmd)
            else:
                if cmd2 > d1:
                    rain2 = rain2-rain3 #(cmd2-d1)-r2
                if rain2>rain:

                    cmd2 = d1

                gamma = (alpha*d2+(1-alpha)*d1)/(d1*d2)
                cmd = cmd2*np.exp(-rain2*gamma)
                u = alpha*(rain2+1.0/d1/gamma*(cmd-cmd2))

            r = rain-(CMD_old-cmd)-u
    
        if cmd > f:
            et = e*evap*np.exp( (1-cmd/f)*2 )
        else:
            et = e*evap

        if et < 0:
            et = 0

        CMD_new = CMD_old + et + u + r - rain
        #print(CMD_old,CMD_new,et,u,r,rain,evap)
        loss = 0
        if Sflow_old+u*area-loss > 0:
            Sflow=1/(1+a)*(Sflow_old+u*area-loss)
            flow=a*Sflow
        else:
            Sflow=Sflow_old+u*area-loss
            flow=0
        #End if

        self.calc_time += time.time() - calc_time

        return CMD_new,flow,Sflow

 #End calcCMD()

    def useUnitHydrograph(self):

        pass
 #End useUnitHydrograph()



