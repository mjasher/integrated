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

    def calcCapitalCosts(self):

        #http://www.g-mwater.com.au/downloads/gmw/Groundwater/Fact_Sheets/11_August_2015_-_DELWP_-_BoreLicence-Consultant-final.pdf
        licence_cost = 235

        total_cost = licence_cost
        return total_cost
    #End calcCapitalCosts()

#End GroundwaterSource()