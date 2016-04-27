# -*- coding: utf-8 -*-
"""
Created on Wed Mar 09 15:50:22 2016

@author: fub
"""

from __future__ import division
from integrated.Modules.Ecology.FlowSuitability import FlowSuitability

import pandas as pd
import numpy as np
import datetime
from datetime import timedelta

class SpeciesFlow(FlowSuitability):
    
    def __init__(self):
        pass
    #End init()
    
    ## component1: calculate low flow index for food and movement
    def calcLowFlowIndex(self, yearly_flow_data, flow_col, summer_low_thd, winter_low_thd,summer_index_thd, winter_index_thd, index_method="linear_scaling"):

        """
        calculate low flow index:
        
        1.  Identify climate condition of the input scenario (dry, average or wet) (TO DO, FOR TOY MODEL JUST USE AS AN INPUT)
        2.  Extract summer and winter low flow thresholds based on climate condition, as per table below:
            
            ============    ============    =============
            Condition       Summer_low      Winter_low
            ============    ============    =============
            Month           Dec-May         Jun-Nov
            Dry climate     >= 10 ML/day    >=50 ML/day
            Avg climate     >= 20 ML/day    >= 100 ML/day
            Wet climate     >= 50 ML/day    >= 200 ML/day
            Minimum days    120 days        60 days
            ============    ============    =============

        3.  For each year calculate the number of days between 1st Dec and 31st May that flow is >= summer low flow threshold, and the number of days between 1st Jun and 30st Nov that flow is >= winter low flow threshold. 
        4.  For each year, if the minimum days for summer AND winter low flows are met, then low flow index for platypus = 1, else, index = 0.
        
        :param yearly_flow_data: Pandas dataframe of daily flow data for the given year in ML/Day
        :param flow_col: Name of flow data column
        :param summer_low_thd: flow threshold (in ML/day) above which summer low flow requirememnt is  satisfied
        :param winter_low_thd: flow threshold (in ML/day) above which winter low flow requirement is satisfied
        :param summer_index_thd: a threshold (in days) above which the number of days summer low are satisfied
        :param winter_index_thd: a threshold (in days) above which the number of days summer low are satisfied      

        :returns: lowflow index with a value of 0 or 1. 

        """
        above_summer_low =  yearly_flow_data[(yearly_flow_data[flow_col] >= summer_low_thd) & (yearly_flow_data.index.month >= 12) | (yearly_flow_data.index.month <= 5)][flow_col].count()
        
        above_winter_low =  yearly_flow_data[(yearly_flow_data[flow_col] >= winter_low_thd) & (yearly_flow_data.index.month >= 6) & (yearly_flow_data.index.month <= 11)][flow_col].count()
        
        
        if index_method == "min_duration":
        #low flow index are calcuated via duration. 
            if (above_summer_low >=summer_index_thd) & (above_winter_low >= winter_index_thd):
                lowflow_index = 1
            else:
                lowflow_index = 0
        if index_method == "linear_scaling":
        # low flow index are calculated based on linear relationshiops between index and number of days above thresholds between 0 and 180, with 180 being rough estimate of the number of days for 6 months.  
            lowflow_index = ((above_summer_low/180)+(above_winter_low/180))/2

        return lowflow_index

    #End calcLowFlowIndex()

    ## component2: calculate summer and autumn freshes for food, and autumn freshes for junenile dispersal.
    def calcFreshIndex(self, yearly_flow_data, flow_col, fresh_thd, durations, frequencies, timing):
        """
        calculate index based on freshes
    
        :param yearly_flow_data: Pandas dataframe of daily flow data for the given year in ML/Day
        :param flow_col: Name of flow data column
        :param fresh_thd: flow threshold (in ML/day) above which is a fresh. 
        :param durations: the fresh duration thresholds (in days) 
        :parm frequencies: the event freqency threshold (in number of events)
        :parm timing: the starting and ending date for a model period (e.g. dispersal)
        
        :returns: food index with a value between 0 and 1. 
        """
        
        flow_conditions = {}
        condition_events = {}
        
        for condition in timing:
            t = timing[condition]
            flow_conditions[condition] = yearly_flow_data[(yearly_flow_data.index >= t["start"]) & (yearly_flow_data.index <= t["end"])]
            
            condition_events[condition] = self.floodEvents(flow_conditions[condition], threshold=fresh_thd[condition], min_separation=0, min_duration=durations[condition])
            
        
        return flow_conditions, condition_events
        
    