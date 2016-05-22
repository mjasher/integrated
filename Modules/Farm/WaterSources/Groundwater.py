from __future__ import division
import WaterSources

class GroundwaterSource(WaterSources.WaterSources):

    """
    The Groundwater Model.
    Could define Groundwater Model here, but probably will be a wrapper to external model
    """
    
    def __init__(self, name, water_level, entitlement, perc_allocation, trade_value_per_ML, cost_per_ML, **kwargs):

        """
        :param water_level: depth below surface
        """
        super(GroundwaterSource, self).__init__(name, water_level, entitlement, perc_allocation, trade_value_per_ML, cost_per_ML)

        #Set all kwargs as class attributes
        for key, value in kwargs.items():
            setattr(self, key, value)
        #End For

    #End init()

    def extractWater(self, water_amount_ML):
        pass
    #End extractWater()

    def calcCapitalCosts(self):

        #http://www.g-mwater.com.au/downloads/gmw/Groundwater/Fact_Sheets/11_August_2015_-_DELWP_-_BoreLicence-Consultant-final.pdf

        #Assume already implemented
        return 0.0
    #End calcCapitalCosts()

#End GroundwaterSource()