from __future__ import division
import WaterSources

class GroundwaterSource(WaterSources.WaterSources):

	"""
	The Groundwater Model.
	Could define Groundwater Model here, but probably will be a wrapper to external model
	"""
	
	def __init__(self, name, water_level):

		"""
		:param water_level: depth below surface
		"""

		self.name = name
		self.water_level = water_level
	#End init()

	def extractWater(self, water_amount_ML):


        
    #End extractWater()

#End GroundwaterSource()