#GwSuitability.py

#import WaterSuitability.WaterSuitability
from WaterSuitability import WaterSuitability
    
class GwSuitability(WaterSuitability):
    
    def GwIndex(self,gw_depth_index, salinity_index):
        """
        Calculate daily groundwater index based on groundwater depth and salinity index
        Output attributes:
        Date, gw_index
        """
        gw_index = gw_depth_index * salinity_index
        return gw_index