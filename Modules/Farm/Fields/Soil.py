from __future__ import division
from integrated.Modules.Core.IntegratedModelComponent import Component

class SoilType(Component):

    """
    Represents soil types

    Needs information on Total Available Water (TAW) for a soil type.
    TAW is the amount of water that a crop can extract from its root zone.

    See:

    http://www.fao.org/docrep/x0490e/x0490e0e.htm

    and Table 3

    http://agriculture.vic.gov.au/agriculture/horticulture/vegetables/vegetable-growing-and-management/estimating-vegetable-crop-water-use


    """

    def __init__(self, name, TAW_mm, current_TAW_mm, group=None):

        """

        :param name: Soil name
        :param TAW_mm: Total Available Water (max capacity) in soil in mm per cubic metre
        :param current_TAW_mm: Water currently in the soil in mm per cubic metre
        :param group: Soil group classification (e.g. Group 1 and 2 - light soils, 3 and 4 - medium soils, etc.)
        """

        self.name = name
        self.TAW_mm = TAW_mm #Total Available Water in soil in mm per cubic metre
        self.current_TAW_mm = current_TAW_mm #Water currently in the soil in mm per cubic metre
        self.group = group #Soil Grouping
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
            current_TAW_mm = self.TAW_mm #self.current_TAW_mm

        #assert current_TAW_mm > 0.0, "Total Available Water in soil cannot be below 0"

        if fraction is None:
            raise ValueError
            # fraction = 0.4
        #End if

        return float(current_TAW_mm) * fraction
        
    #End calcRAW()

    # def updateTAW(self, c_swd):

    #     """
    #     :param c_swd: Current soil water deficit
    #     """

    #     if self.current_TAW_mm < self.TAW_mm:
    #         if (self.current_TAW_mm + c_swd) > self.TAW_mm:
    #             # seepage = (self.current_TAW_mm + c_swd) - c_swd
    #             self.current_TAW_mm = self.TAW_mm
    #         else:
    #             self.current_TAW_mm = self.current_TAW_mm + c_swd
    #             # seepage = c_swd
    #         #End
    #     #End if
    # #End updateTAW()

    
#End SoilType()