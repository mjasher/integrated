from __future__ import division
import pandas as pd
from integrated.Modules.Core.IntegratedModelComponent import Component
from integrated.Modules.Core.Handlers.FileHandler import FileHandler

class Routing(Component):

	def __init__(self, Climate, water_volume):

		"""
		Climate : Climate Data in Pandas DataFrame
		water_volume : S_{k-1}, starting water level/storage as a volume
		"""

		self.Climate = Climate
		self.water_volume = water_volume

	def run(self):

		pass
	#End run

	def calcFlow(self, prev_storage, inflow, irrig_out, evap, local_inflow, base_flow, deep_drainage, storage_coef, ET_f):

		"""
		prev_storage : S_{k}, storage level at previous node
		inflow : f_{k} inflow to reach (from upstream reaches)
		outflow: O_{k} Outflow
		irrig_out : I_{k}, irrigation extraction
		evap : E_{k}, potential evapotranspiration
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
		#self.Climate

		Gamma_k = base_flow - deep_drainage #These could come from external module

		#O_{k} = aS_{k} if S_{k} > 0 else 0
		outflow = storage_coef*self.water_volume if self.water_volume > 0 else 0

		self.water_volume = self.water_volume + (inflow + local_inflow + Gamma_k) - (ET_f*evap) - irrig_out - outflow

		return self.water_volume

	#End calcFlow()






