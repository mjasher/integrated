from __future__ import division
from integrated.Modules.Ecology.SpeciesFlow import SpeciesFlow

import pandas as pd
#import numpy as np
import datetime
from datetime import timedelta

class PlatypusFlow(SpeciesFlow):

    def __init__(self):
        pass

    #End init()

    def calcFoodDispIndex(self, yearly_flow_data, flow_col, fresh_thd, durations, frequencies, timing):
        """
        calculate food index
        1.For each ecology year, identify three model periods (1 Dec-28 Feb; 1 Mar-31 May; 1 Apr-31 May)
        2.Calculate the number of events. The events are defined as if the flow is above the fresh threshold depending on climate, and the minimum duration depend on the start date of the event.
                    
            ============    ============    =============    =============
            Condition       Summer_food      Autumn_food       Dispersal  
            ============    ============    =============    =============
            Dry climate                  >= 50 ML/days                    
            Avg climate                  >= 75 ML/day                     
            Wet climate                  >= 125 ML/days                   
            Month             Dec-Feb         Mar-May           Apr-May
            Duration         >= 1 day        >= 2 days        >= 2 days
            Frequency        >= 1 event      >= 2 events      >= 2 events
            ============    ============    =============    =============
        
        3. Calculate food index. The index is 1 when summer and autumn food event frequency are met; 0.5 being the frequency for summer and autumn food are partially met; Otherwise, it is 0.
        4. Calculate dispersal index. The index is 1 when there are at least 2 events; 0.5 when 1 event; Otherwise, it is 0.
             
        :param yearly_flow_data: Pandas dataframe of daily flow data for the given year in ML/Day
        :param flow_col: Name of flow data column
        :param fresh_thd: flow threshold (in ML/day) above which is a fresh. 
        :param durations: the fresh duration thresholds (in days) 
        :parm frequencies: the event freqency threshold (in number of events)
        :parm timing: the starting and ending date for a model period (e.g. dispersal)
        
        :returns: food index with a value between 0 and 1. 
        """
        
        flow_conditions, condition_events = self.calcFreshIndex(yearly_flow_data, flow_col, fresh_thd, durations, frequencies, timing)
        
        summer_food_events = condition_events["summerfood"]
        autumn_food_events = condition_events["autumnfood"]
        dispersal_events = condition_events["dispersal"]
       
        summer_freq_thd = frequencies["summerfood"]
        autumn_freq_thd = frequencies["autumnfood"]
       
       
        if (len(summer_food_events) == 0) and (len(autumn_food_events) == 0):
            food_index = 0
        elif (len(summer_food_events) >= summer_freq_thd) and (len(autumn_food_events) >= autumn_freq_thd):
            food_index = 1
        else:
            food_index = 0.5
        
        if len(dispersal_events) == 0 :
            dispersal_index = 0
        elif len(dispersal_events) >= autumn_freq_thd:
            dispersal_index = 1
        else:
            dispersal_index = 0.5

        return food_index, dispersal_index
    #End calcFoodDispIndex
        
        

    ## component4: calcualte the index for burrow flooding
    def calcBurrowIndex(self, yearly_flow_data, flow_col, burrow_startmonth, burrow_endmonth, entrance_buffer, breeding_startmonth, breeding_endmonth):

        """
        Given specs:
        1. Within each burrowing season window (1 July-31 Aug), identify max flow level (ML/day).   
        2. Calculate the platypus flow benchmark for this season: benchmark = max flow (ML/day) + burrow buffer (x ML/day). x ranges from 0 to a certain positive number to account for platypus barrow a little above the max flow.
        3. Following each burrowing season, scan the breeding season (1st Sep-28th Feb), events are identified if flow reaches above the benchmark. 
        4. The longest event is used to calculate burrow flood index. If the duration of the duration is below or equal 1 days, the index is 1 (indicating the event is fine for platypus); if the duration is between 2-3 days, the index is 0.5, indicating a lower preference due to risk of drowning; if duration is 4 days or above, the index value is zero indicating the worst outcome for platypus due to flooding of the burrows.
        
        :param yearly_flow_data: Pandas dataframe of daily flow data for the given year in ML/Day
        :param flow_col: Name of flow data column
        :param burrow_startmonth: the starting month of platypus burrowing period
        :param burrow_endmonth: the end month of platypus burrowing period, 
        :param entrance_buffer: some buffer (ML/day) to add to max flow, allowing burrow entrance to be slightly higher than the max flow level
        :param breeding_startmonth: the starting month of platypus breeding period
        :param breeding_endmonth: the ending month of platypus breeding period
        
        :returns: burrow index with a value of 0 or 1

        """
        year = yearly_flow_data.index.year[0]
        burrow_start = pd.to_datetime(datetime.date(year, burrow_startmonth, 1))
        burrow_end = pd.to_datetime(datetime.date(year, burrow_endmonth+1, 1)) - timedelta(days=1) #+1 to move to the beginning of next month, then -1 to move back a day so that 30th/31st can be accounted for.   
        burrow_flow = yearly_flow_data[(yearly_flow_data.index >= burrow_start) & (yearly_flow_data.index <= burrow_end)]
        max_flow = burrow_flow[flow_col].max()
        burrow_benchmark = max_flow + entrance_buffer
        
        
        breeding_start = pd.to_datetime(datetime.date(year, breeding_startmonth, 1))
        breeding_end = pd.to_datetime(datetime.date(year+1, breeding_endmonth+1, 1)) - timedelta(days=1)
        breeding_flow = yearly_flow_data[(yearly_flow_data.index >= breeding_start) & (yearly_flow_data.index <= breeding_end)]
        
        
        flood_events = self.floodEvents(breeding_flow, threshold=burrow_benchmark, min_separation=0, min_duration=1)
        
        if len(flood_events) == 0:
            burrow_index = 1
        else:
            max_flood_duration = flood_events['duration'].max()
        
            if max_flood_duration <= 2:
                burrow_index = 1
            elif max_flood_duration >= 4:
                burrow_index = 0
            else:
                burrow_index = 0.5

        return burrow_index

    #End calcFlowBenchmark()
    
#End Platypus