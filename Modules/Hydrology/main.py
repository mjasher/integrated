import pandas as pd
from integrated.Modules.Core.IntegratedModelComponent import Component

class Hydrology():

	__init__(self, Climate, parameters, network):
		

		"""
		parameters: Dict of IHACRES, Routing, Dam, Network parameters
		"""

		# parameters = {
		# 	"IHACRES": None,
		# 	"Routing": None,
		# 	"Dam": None,
		# 	"Network": None
		# }

	#End init()

	def run(self):
		pass

	def calcFlow(self, cat_SWD):
		pass

	def overflow(self):
		pass

	def release(self):
		pass

	def infiltration(self):
		pass

	def calcStorage(self):
		pass
