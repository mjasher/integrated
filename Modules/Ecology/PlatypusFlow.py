from __future__ import division
from integrated.Modules.Ecology.FlowSuitability import FlowSuitability

import pandas as pd
import numpy as np
import datetime

class PlatypusFlow(FlowSuitability):

	def __init__(self):
		pass

	#End init()

## component1: calculate low flow index for food and movement
	def calcLowFlowIndex(self, yearly_flow_data, flow_col, summer_low_thd, winter_low_thd,summer_index_thd, winter_index_thd):

		"""
		calculate low flow index
		"""

		above_summer_low =  yearly_flow_data[yearly_flow_data[flow_col] >= summer_low_thd & yearly_flow_data.index.month >= 12 & yearly_flow_data.index.month <= 5][flow_col].count()

		above_winter_low =  yearly_flow_data[yearly_flow_data[flow_col] >= winter_low_thd & yearly_flow_data.index.month >= 6 & yearly_flow_data.index.month <= 11][flow_col].count()

		if above_summer_low >=summer_index_thd & above_winter_low >= winter_index_thd:
			lowflow_index = 1
		else:
			lowflow_index = 0

		return lowflow_index

	#End calcHabitatIndex()
 
 ## component2: calculate summer and autumn freshes for food
 
 
 ## component3: calcualte autumn freshes for junenile dispersal
 
 
 ## component4: calcualte the index for burrow flooding
 	def calcFlowBenchmark(self, yearly_flow_data, flow_col, season_start, burrow_window, season_end, level_buffer):

		"""
		Given specs:
		1.	For each daily flow time series (at each gauge location), identify season windows
		2.	Within each season window, identify beginning season window
		3.	Within each beginning season window, identify max flow level (ML/day). 
		4.	Calculate the platypus flow 'benchmark' for this season: benchmark = max flow + x . x ranges from 0 to a certain positive number to account for platypus barrow a little above the max flow.
		5.	Scan the rest of the flow sequence within the season window and calculate the number of days (or proportion of days) the flow is above the 'benchmark'. This is the output. 


		:param yearly_flow_data: Pandas dataframe of daily flow data for the given year in ML/Day
		:param flow_col: Name of flow data column
		:param start_season: Day of year that breeding/burrow season starts
		:param burrow_window: Number of days to base benchmark on
		:param season_end: Day of year that correspond to end of season
		:param level_buffer: The :math:`x` metres to add to max flow

		:returns: Dict, e.g. {'num_days_above_benchmark': 101, 'proportion_of_season': 0.6733, 'benchmark': 47.52}

		"""

		year = yearly_flow_data.index.year[0]
		
		dt_start = datetime.date(year, 1, 1) + datetime.timedelta(days=season_start)
		dt_start = pd.to_datetime(dt_start)

		dt_end = datetime.date(year, 1, 1) + datetime.timedelta(days=season_end)
		dt_end = pd.to_datetime(dt_end)

		burrow_window_end = datetime.date(year, 1, 1) + datetime.timedelta(days=(season_start+burrow_window))
		burrow_window_end = pd.to_datetime(burrow_window_end)

		year_index = yearly_flow_data.index
		breeding_time = yearly_flow_data[(year_index >= dt_start) & (year_index <= burrow_window_end)]

		max_flow = breeding_time[flow_col].max()

		flow_benchmark = max_flow + level_buffer

		post_burrow = yearly_flow_data[(year_index > burrow_window_end) & (year_index <= dt_end)]

		num_days_above_benchmark = post_burrow[post_burrow[flow_col] >= flow_benchmark][flow_col].count()
		proportion = num_days_above_benchmark / (season_end - season_start)

		benchmark_df = pd.DataFrame(index=[year])
		benchmark_df['num_days_above_benchmark'] = num_days_above_benchmark
		benchmark_df['proportion_of_season'] = proportion
		benchmark_df['flow_benchmark'] = flow_benchmark

		return benchmark_df

	#End calcFlowBenchmark()



	
#End Platypus