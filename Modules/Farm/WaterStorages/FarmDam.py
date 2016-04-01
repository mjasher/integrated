from __future__ import division
from WaterStore import WaterStore

#from WaterStorages.WaterStore import WaterStore
#from Common.GeneralFunctions import *
from integrated.Modules.Core.GeneralFunctions import *


class FarmDam(WaterStore):

    """
    Defines a farm dam
    """

    def __init__(self, include_farm_dam_capital_costs=True, **kwargs):

        self.include_farm_dam_capital_costs = include_farm_dam_capital_costs
        self.pump_vol_ML = kwargs.pop('pump_vol_ML', 0)

        WaterStore.__init__(self, **kwargs)

        #self.calcNetWaterAvailable()
        self.annual_cost = self.calcAnnualCosts()

    #End init()

    def calcNetWaterAvailable(self):

        available_water = self.WaterSources.calcGrossWaterAvailable()
        #self.net_water_available = available_water - (available_water * self.ClimateVariables.surface_evap_rate)

        return (available_water - (available_water * self.ClimateVariables.surface_evap_rate))

    #End calcNetWaterAvailable()

    def calcTotalCapitalCosts(self):

        """
        Calculate total cost of this storage solution
        """

        #In original code, it would set include_farm_dam_capital_costs to 0
        #and multiply surface_storage_cost by include_farm_dam_capital_costs
        #i.e. (storage_cost_per_ML * total_surface_water) * include_farm_dam_capital_costs
        #   = (storage_cost_per_ML * total_surface_water) * 0

        # total_surface_water = self.WaterSources.water_source['flood_harvest']

        if self.include_farm_dam_capital_costs is True:
            #return self.storage_cost_per_ML * total_surface_water
            return self.storage_cost_per_ML * self.storage_capacity_ML
        else:
            return 0
        #End if

    #End calcStorageCapitalCosts()

    def calcTotalCapitalCostsPerHa(self, area):
        return self.calcTotalCapitalCosts() / area

    def calcCapturePumpCostPerML(self, stored_water_ML):
        return self.pump_cost_dollar_per_ML * self.capture_pump_cost_ratio
    #End calcCapturePumpCostPerML

    def calcOngoingCosts(self):

        """
        Calculate ongoing costs of this storage practice, for a given year
        """

        pump_cost = self.calcPumpCost(self.pump_vol_ML)
        stored_water_ML = self.stored_water_vol_ML #self.WaterSources.water_source['flood_harvest']
        surface_pump_cost = self.calcSurfacePumpCost(stored_water_ML)
        maintenance_cost = self.calcMaintenanceCosts(stored_water_ML)

        #print pump_cost, surface_pump_cost, maintenance_cost

        ongoing_cost = pump_cost + maintenance_cost + surface_pump_cost

        return ongoing_cost

    #End calcCapitalCosts()

    def calcAnnualCosts(self):

        """
        Calculate the annual cost of the given storage solution
        #total_surface_water: 200ML flood water harvest, 25 percent of recent statutory limits
        """

        capital_cost = self.calcTotalCapitalCosts()
        ongoing_cost = self.calcOngoingCosts()

        cost = calcCapitalCostPerYear(capital_cost, self.discount_rate, self.num_years) + ongoing_cost

        self.annual_cost = cost

        return cost

    #End calcCosts()

#End SurfaceStorage
