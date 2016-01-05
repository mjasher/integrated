from __future__ import division
import pandas as pd 
from integrated.Modules.Core.IntegratedModelComponent import Component

class Dam():

	__init__(self, Climate, parameters, network):
		

		"""
		parameters: Dict of IHACRES, Routing, Dam, Network parameters
		"""

		self.Climate = Climate
		self.parameters = parameters
		self.network = network

		# parameters = {
		# 	"IHACRES": None,
		# 	"Routing": None,
		# 	"Dam": None,
		# 	"Network": None
		# }

	#End init()

	def run(self):
		"""
		Outputs

		Outflow and Storage
		O_{k}, S_{k}
		"""
	#End run()

	def overflow(self):

		"""
		f(S_{k})
		"""

		pass

	def release(self):
		pass

	def infiltration(self):

		#self.water_level
		"""
		g*(S_{k})
		"""

		pass

	def calcStorage(self):
		pass

	def calc(self, inflow, rainfall, evap, infil, recharge, spill, area):

		"""

		S_{k} : Current node

		inflow : f_{k} from IHACRES

		rainfall : p_{k} from Climate

		evap : E_{k} from Climate

		infil : I_{k}, an equation - depends on water depth

		recharge : R_{k}, from integrated model

		spill : O_{k}
		"""

		#S_{k} = S_{k-1} + inflow + rainfall*area - evap*area - infil*area - recharge*area - spill
