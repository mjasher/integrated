from __future__ import division
from integrated.Modules.Ecology.SpeciesFlow import SpeciesFlow

#import pandas as pd
#import numpy as np
#import datetime
#from datetime import timedelta

class FishFlow(SpeciesFlow):
    
    def __init__(self):
        pass
    #End init()
        
    def calcSpawnIndex(self, yearly_flow_data, flow_col, fresh_thd, durations, frequencies, timing):
                
        flow_conditions, condition_events = self.calcFreshIndex(yearly_flow_data, flow_col, fresh_thd, durations, frequencies, timing)
        spawn_events = condition_events["spawning"]
        dispersal_events = condition_events["dispersal"]
        washout_events = condition_events["washout"]
        
        spawn_freq_thd = frequencies["spawning"]
        dispersal_freq_thd = frequencies["dispersal"]
        washout_freq_thd = frequencies["washout"]      
       
        if len(spawn_events) == 0 :
            spawn_index = 0
        elif len(spawn_events) >= spawn_freq_thd:
            spawn_index = 1
        else:
            spawn_index = 0.5
        
        
        if len(dispersal_events) == 0 :
            dispersal_index = 0
        elif len(dispersal_events) >= dispersal_freq_thd:
            dispersal_index = 1
        else:
            dispersal_index = 0.5
                  
        if len(washout_events) == 0 :
            washout_index = 1
        elif len(washout_events) >= washout_freq_thd:
            washout_index = 0
        else:
            washout_index = 0.5     

        return spawn_index, dispersal_index, washout_index
    #End calcFoodDispIndex