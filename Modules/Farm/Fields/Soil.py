from integrated.Modules.Core.IntegratedModelComponent import Component

class SoilType(Component):

	"""
	Represents soil types
	"""

	def __init__(self, name, TAW_mm, current_TAW_mm):
		self.name = name
		self.TAW_mm = TAW_mm #Total Available Water in soil in mm per cubic metre
		self.current_TAW_mm = current_TAW_mm #Water currently in the soil in mm per cubic metre
	#End __init__()

	def calcRAW(self, current_TAW_mm=None, fraction=None):

		"""
		Calculate Readily Available Water in mm per metre depth

		If TAW_mm or fraction coefficient is not passed to this function it will use the values given at object instantiation.

		Explanation of TAW and RAW
		http://www.fao.org/docrep/x0490e/x0490e0e.htm

		:param TAW_mm: Total Available Water in mm
		:param fraction: Depletion Fraction Coefficient to use for specified soil type

		"""

		if current_TAW_mm is None:
			current_TAW_mm = self.current_TAW_mm

		if fraction is None:
			fraction = 0.4

		return float(current_TAW_mm) * float(fraction)
		
	#End calcRAW()

	
#End SoilType()