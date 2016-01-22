from __future__ import division
from integrated.Modules.Ecology.FlowSuitability import FlowSuitability

import pandas as pd
import numpy as np
import datetime
from datetime import timedelta

class PlatypusFlow(FlowSuitability):

	def __init__(self):
		pass

	#End init()

## component1: calculate low flow index for food and movement
	def calcLowFlowIndex(self, yearly_flow_data, flow_col, summer_low_thd, winter_low_thd,summer_index_thd, winter_index_thd):

		"""
		calculate low flow index:
		1.	Identify climate condition of the input scenario (dry, average or wet) (TO DO, FOR TOY MODEL JUST USE AS AN INPUT)
		2.	Extract summer and winter low flow thresholds based on climate condition, as per table below:
				Summer_low	Winter_low
			Month	Dec-May	Jun-Nov
			Dry climate	>= 10 ML/day	>=50 ML/day
			Average climate	>= 20 ML/day	>= 100 ML/day
			Wet climate	>= 50 ML/day	>= 200 ML/day
			Minimum days	 150 days	150 days
		3.	For each year calculate the number of days between 1st Dec and 31st May that flow is >= summer low flow threshold, and the number of days between 1st Jun and 30st Nov that flow is >= winter low flow threshold. 
		4.	For each year, if the minimum days for summer AND winter low flows are met, then low flow index for platypus = 1, else, index = 0.
		
		:param yearly_flow_data: Pandas dataframe of daily flow data for the given year in ML/Day
		:param flow_col: Name of flow data column
		:param summer_low_thd: flow threshold (in ML/day) above which summer low flow requirememnt is  satisfied
		:param winter_low_thd: flow threshold (in ML/day) above which winter low flow requirement is satisfied
		:param summer_index_thd: a threshold (in days) above which the number of days summer low are satisfied
		:param winter_index_thd: a threshold (in days) above which the number of days summer low are satisfied		

		:returns: lowflow index with a value of 0 or 1. 

		"""
		above_summer_low =  yearly_flow_data[(yearly_flow_data[flow_col] >= summer_low_thd) & (yearly_flow_data.index.month >= 12) | (yearly_flow_data.index.month <= 5)][flow_col].count()
		above_winter_low =  yearly_flow_data[(yearly_flow_data[flow_col] >= winter_low_thd) & (yearly_flow_data.index.month >= 6) | (yearly_flow_data.index.month <= 11)][flow_col].count()

		if (above_summer_low >=summer_index_thd) & (above_winter_low >= winter_index_thd):
			lowflow_index = 1
		else:
			lowflow_index = 0

		return lowflow_index

	#End calcHabitatIndex()
 
 ## component2: calculate summer and autumn freshes for food
 
 
 ## component3: calcualte autumn freshes for junenile dispersal.
 
 
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
		
		max_flood_duration = self.floodEvents(breeding_flow, threshold=burrow_benchmark, min_separation=0, min_duration=1)['duration'].max()

		## for test run, comment it when running script	
		# max_flood_duration = PlatypusFlow().floodEvents(breeding_flow, threshold=burrow_benchmark, min_separation=0, min_duration=1)['duration'].max()
		
		if max_flood_duration == 2:
			burrow_index = 1
		elif max_flood_duration >= 4:
			burrow_index = 0
		else:
			burrow_index = 0.5

		return burrow_index

	#End calcFlowBenchmark()



	
#End Platypus