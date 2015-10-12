from WaterStore import WaterStore
#from GeneralFunctions import *


class BasinStorage(WaterStore):

    """
    Defines Basin infiltration storage
    """

    def __init__(self, **kwargs):

        """
        Basin Storage system

        Basin specific variables

        MAR_ML
        MAR_loss_rate

        cost_temp_storage_per_ML
        cost_treatment_capital_cost
        cost_treatment_per_ML
        cost_of_design_as_proportion_of_capital
        infiltration_rate  (defaults to 0.2)
        capital_cost_per_ML_at_02_per_day (defaults to 363)
        capital_cost_per_ML

        design_cost reflects the cost of designing a Basin storage system, as a proportion of total capital cost

        """

        WaterStore.__init__(self, **kwargs)

        self.MAR_ML = self.WaterSources.calcGrossWaterAvailable()

        self.MAR_loss_rate = kwargs.pop('MAR_loss_rate', 0.05)
        self.capital_cost_per_ML_at_02_per_day = kwargs.pop('capital_cost_per_ML_at_02_per_day', 363)
        self.cost_of_design_as_proportion_of_capital = kwargs.pop('cost_of_design_as_proportion_of_capital', 0.1)

        self.cost_temp_storage_per_ML = kwargs.pop('cost_temp_storage_per_ML', 0)

        self.capital_cost_treatment_per_ML = kwargs.pop('capital_cost_treatment_per_ML', 250)
        self.cost_treatment_per_ML = kwargs.pop('cost_treatment_per_ML', 150)
        self.capital_cost_treatment = kwargs.pop('capital_cost_treatment', (self.capital_cost_treatment_per_ML * self.storage_capacity_ML))

        self.infiltration_rate = kwargs.pop('infiltration_rate', 0.2)
        self.capture_pump_cost_ratio = kwargs.pop('capture_pump_cost_ratio', 0.6)

        self.capital_cost_per_ML = kwargs.pop('capital_cost_per_ML', self.calcStorageCapitalCostPerML(self.capital_cost_per_ML_at_02_per_day))
        self.cost_capital = kwargs.pop('cost_capital', self.calcStorageCapitalCosts())

        #Calculate derived parameters
        
        self.design_cost = kwargs.pop('design_cost', self.calcDesignCosts())

        #self.net_water_available = self.MAR_ML - (self.MAR_loss_rate * self.MAR_ML)
        self.calcNetWaterAvailable()

        self.updatePumpVolML()

        self.annual_cost = self.calcAnnualCosts()

    #End init()

    def calcNetWaterAvailable(self):

        self.MAR_ML = self.WaterSources.calcGrossWaterAvailable()
        self.net_water_available = self.MAR_ML - (self.MAR_loss_rate * self.MAR_ML)

        return self.net_water_available

    #End calcNetWaterAvailable()

    def updatePumpVolML(self):

        """
        Update pump vol per ML after MAR loss rate or MAR capacity has been updated
        """

        self.pump_vol_ML = (1 - self.MAR_loss_rate) * self.MAR_ML
    #End updatePumpVolML()

    def calcTemporaryStorageCosts(self):

        temporary_storage_cost = self.cost_temp_storage_per_ML * self.storage_capacity_ML

        return temporary_storage_cost

    #End calcTemporaryStorageCosts()

    def calcStorageCapitalCostPerML(self, capital_cost_per_ML_at_02_per_day=None, modifier=0.2):

        if capital_cost_per_ML_at_02_per_day is None:
            capital_cost_per_ML_at_02_per_day = self.capital_cost_per_ML_at_02_per_day

        capital_cost_per_ML = capital_cost_per_ML_at_02_per_day * (modifier/self.infiltration_rate)

        return capital_cost_per_ML

    #End calcStorageCapitalCostPerML()

    def calcStorageCapitalCosts(self):

        return (self.calcStorageCapitalCostPerML() * self.storage_capacity_ML)

    #End calcStorageCapitalCost()

    def calcTotalCapitalCosts(self):

        capital_cost = self.calcDesignCosts() + self.calcStorageCapitalCosts() + self.calcTemporaryStorageCosts()

        return capital_cost

    #End calcCapitalCosts()

    def calcDesignCosts(self):

        design_cost = self.calcStorageCapitalCosts() * self.cost_of_design_as_proportion_of_capital

        return design_cost

    #End calcDesignCosts

    def calcOngoingCosts(self):

        surface_pump_cost = self.calcSurfacePumpCost(self.MAR_ML)

        ongoing_cost = (self.maintenance_rate * self.calcStorageCapitalCosts()) + surface_pump_cost + self.calcPumpCost(self.pump_vol_ML)

        return ongoing_cost

    #End calcOngoingCosts()

    def calcAnnualCosts(self):

        capital_cost = self.calcTotalCapitalCosts()

        ongoing_cost = self.calcOngoingCosts()

        cost = calcCapitalCostPerYear(capital_cost, self.discount_rate, self.num_years) + ongoing_cost

        self.annual_cost = cost

        return cost

    #End calcAnnualCosts()

#End BasinStorage
