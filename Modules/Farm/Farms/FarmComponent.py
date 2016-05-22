from __future__ import division
from integrated.Modules.Core.IntegratedModelComponent import Component

class FarmComponent(Component):

    """
    Interface Class for Farm Components.
    All methods defined here should be redefined by implementing child classes.
    """

    def __init__(self, implemented=False):
        self.implemented = implemented
    #End init()

    def calcTotalCostsPerHa(self):

        """
        Cost of implementation and operation
        """

        pass
    #End calcTotalCosts()

    def calcGrossMarginsPerHa(self):
        pass
    #End calcGrossMargins()

    def calcOperationalCostPerHa(self):
        """
        Calculate cost of operation per year
        """
        pass
    #End calcOperationalCostPerHa()

    def calcImplementationCostPerHa(self):
        """
        Calculate the capital cost 
        """
        pass
    #End calcImplementationCostPerHa()