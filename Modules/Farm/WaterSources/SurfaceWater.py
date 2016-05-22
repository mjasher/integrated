from __future__ import division
import WaterSources

class SurfaceWaterSource(WaterSources.WaterSources):

    def __init__(self, name, water_level, entitlement, perc_allocation, trade_value_per_ML, cost_per_ML, **kwargs):
        super(SurfaceWaterSource, self).__init__(name, water_level, entitlement, perc_allocation, trade_value_per_ML, cost_per_ML)

        #Set all kwargs as class attributes
        for key, value in kwargs.items():
            setattr(self, key, value)
        #End For

    #End init()

    def calcCapitalCosts(self):

        #Assume already implemented
        return 0.0
    #End calcCapitalCosts()

#End SurfaceWaterSource()