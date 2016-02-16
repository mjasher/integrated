from __future__ import division
import WaterSources

class GroundwaterSource(WaterSources.WaterSources):

    """
    The Groundwater Model.
    Could define Groundwater Model here, but probably will be a wrapper to external model
    """
    
    def __init__(self, name, water_level, entitlement, water_value_per_ML, cost_per_ML, **kwargs):

        """
        :param water_level: depth below surface
        """
        super(GroundwaterSource, self).__init__(name, water_level, entitlement, water_value_per_ML, cost_per_ML)
    #End init()

    def extractWater(self, water_amount_ML):
        pass
    #End extractWater()

#End GroundwaterSource()