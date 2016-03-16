from __future__ import division
from integrated.Modules.Core.IntegratedModelComponent import Component

class FarmComponent(Component):

	"""
	Interface Class for Farm Components.
	All methods defined here should be redefined by implementing child classes.
	"""

	def __init__(self, implemented=False):
		self.implemented = implemented
	#End init()

	def calcTotalCostsPerHa(self):
		pass
	#End calcTotalCosts()

	def calcGrossMarginsPerHa(self):
		pass
	#End calcGrossMargins()

	def calcOperationalCostPerHa(self):
		pass
	#End calcOperationalCostPerHa()

	def calcImplementationCostPerHa(self):
		pass
	#End calcImplementationCostPerHa()