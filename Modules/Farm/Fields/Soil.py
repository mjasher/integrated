from Modules.Core.IntegratedModelComponent import Component

class SoilType(Component):

	"""
	Represents soil types
	"""

	def __init__(self, name, TAW_mm):
		self.name = name
		self.TAW_mm = TAW_mm #Total Available Water in soil in mm per metre of soil depth
	#End __init__()

	def calcRAW(self, TAW_mm=None, fraction=None):

		"""
		Calculate Readily Available Water in mm per metre depth
		"""

		if TAW_mm is None:
			TAW_mm = self.TAW_mm

		if fraction is None:
			fraction = 0.5

		return TAW_mm * fraction
		
	#End calcRAW()

	
#End SoilType()