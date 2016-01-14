from __future__ import division
import pandas as pd
from integrated.Modules.Core.IntegratedModelComponent import Component
from integrated.Modules.Core.Handlers.FileHandler import FileHandler

class Routing(Component):

	def __init__(self, Climate, water_volume):

		"""
		Climate : Climate Data in Pandas DataFrame
		water_volume : S_{k-1}, starting water level/storage as a volume as a data series
		"""

		self.Climate = Climate
		self.water_volume = water_volume

		print self.water_volume

	def run(self):

		pass
	#End run

	def calcFlow(self, node_id, climate, prev_storage, inflow, irrig_ext, local_inflow, base_flow, deep_drainage, storage_coef, ET_f):

		"""
		climate: Climate data for node
			evap : E_{k}, potential evapotranspiration (taken from climate)

		prev_storage : S_{k}, storage level at previous timestep
		inflow : f_{k} inflow to reach (from upstream reaches)
		outflow: O_{k} Outflow
		irrig_ext : I_{k}, irrigation extraction
		
		local_inflow : q_{k}, flow from subcatchment area, from IHACRES
		base_flow : B_{k}, base flow dependent on soil deficit
		deep_drainage: D_{k}

		storage_coef : Storage coefficient, a
		ET_f : ET Factor or Crop Factor, w

		Flow is in ML/day
		Irrigation in ML/day
		Evaporation in ML/day

		returns: 
			Current storage S_{k}, Outflow, Irrigation outflow

		"""

		#ET_f and evap parameters may come from the Climate dataset
		#climate
		# ET_f = climate['evap']
		# storage_coef = 0.5

		evap = climate['evap'].iloc[0]

		Gamma_k = base_flow - deep_drainage #These could come from external module

		#O_{k} = aS_{k} if S_{k} > 0 else 0

		water_info = self.water_volume[self.water_volume['node'] == node_id].iloc[0]

		outflow = storage_coef*water_info["water_volume"] if water_info["water_volume"] > 0 else 0

		water_volume = water_info["water_volume"] + (inflow + local_inflow + Gamma_k) - (ET_f*evap) - irrig_ext - outflow

		return water_volume

	#End calcFlow()






