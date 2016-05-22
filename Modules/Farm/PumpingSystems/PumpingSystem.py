#PumpingSystem

from integrated.Modules.Farm.Farms.FarmComponent import FarmComponent

class Pumps(FarmComponent):

    def __init__(self, **kwargs):
        #Set all kwargs as class attributes
        for key, value in kwargs.items():
            setattr(self, key, value)
        #End For

        self.implemented = True

        #self.years_in_operation = 0 #TODO: factor in major maintenance cost rates
    #End init()

    def calcOperationalCostPerHa(self, area):
        """
        Calculate yearly cost of operation (maintenance costs, etc.)
        """
        maintenance = self.capital_cost * self.minor_maintenance_rate

        return maintenance / area
    #End calcOperationalCostPerHa()

    def calcImplementationCostPerHa(self, area):
        """
        Calculate the capital cost 
        """

        return self.capital_cost / area

    #End calcImplementationCostPerHa()

    def calcTotalCostsPerHa(self, area):

        """
        Cost of implementation and operation
        """

        costs = self.calcImplementationCostPerHa(area) if self.implemented == False else 0
        costs += self.calcOperationalCostPerHa(area)

        return costs

    #End calcTotalCosts()    

