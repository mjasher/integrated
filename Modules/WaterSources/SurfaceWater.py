import WaterSources

class SurfaceWaterSource(WaterSources.WaterSources):

	def __init__(self, name, water_level, entitlement, water_value_per_ML, cost_per_ML, **kwargs):
		super(SurfaceWaterSource, self).__init__(name, water_level, entitlement, water_value_per_ML, cost_per_ML)

	#End init()

#End SurfaceWaterSource()