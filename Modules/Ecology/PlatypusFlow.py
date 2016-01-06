from __future__ import division
from integrated.Modules.Ecology.FlowSuitability import FlowSuitability

import pandas as pd
import numpy as np
import datetime

class PlatypusFlow(FlowSuitability):

	def __init__(self):
		#Call parent constructor
		FlowSuitability.__init__(self)

	#End init()

	def calcFlowBenchmark(self, yearly_flow_data, flow_col, season_start, burrow_window, season_end, level_buffer):

		"""
		1.	For each daily flow time series (at each gauge location), identify season windows
		2.	Within each season window, identify beginning season window
		3.	Within each beginning season window, identify max flow level (ML/day). 
		4.	Calculate the platypus flow 'benchmark' for this season: benchmark = max flow + x . x ranges from 0 to a certain positive number to account for platypus barrow a little above the max flow.
		5.	Scan the rest of the flow sequence within the season window and calculate the number of days (or proportion of days) the flow is above the 'benchmark'. This is the output. 


		:param flow_data: Pandas dataframe of daily flow data for the given year
		:param flow_col: Name of flow data column
		:param start_season: Day of year that breeding/burrow season starts
		:param burrow_window: Number of days to base benchmark on
		:param season_end: Day of year that correspond to end of season
		:param level_buffer: The :math:`x` metres to add to max flow

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

		num_days_above_benchmark = post_burrow[post_burrow[flow_col] > flow_benchmark][flow_col].count()
		proportion = num_days_above_benchmark / (season_end - season_start)

		return {'num_days_above_benchmark': num_days_above_benchmark, 'proportion_of_season': proportion}

		
	#End calcFlowBenchmark()
	
#End Platypus