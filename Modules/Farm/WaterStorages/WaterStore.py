#WaterStorage.py

class WaterStore(object):

    """
    Defines a water store
    """

    def __init__(self, **kwargs):

        """
        name: name of Water Storage Practice
        storage_capacity_ML: Storage capacity in ML
        storage_cost_per_ML: Cost of storage per ML
        cost_capital: How much it costs to change to this storage type
        maintenance_rate: cost of maintenance for this storage type
        pump_cost_dollar_per_ML: how much it costs to pump water = $35
        discount_rate: Rate at which future returns have to be decreased by to be comparable with present value; 7 percent
        """

        self.name = kwargs.pop('name', 'Farm Dam')
        self.num_years = kwargs.pop('num_years', 30)
        self.storage_capacity_ML = kwargs.pop('storage_capacity_ML', 200)
        self.storage_cost_per_ML = kwargs.pop('storage_cost_per_ML', 1000)
        self.cost_capital = kwargs.pop('cost_capital', 0)
        self.maintenance_rate = kwargs.pop('maintenance_rate', 0.005)
        self.capture_pump_cost_ratio = kwargs.pop('capture_pump_cost_ratio', 0.5)
        self.pump_cost_dollar_per_ML = kwargs.pop('pump_cost_dollar_per_ML', 35)
        self.discount_rate = kwargs.pop('discount_rate', 0.07)

        self.WaterSources = kwargs.pop('WaterSources', None)
        self.ClimateVariables = kwargs.pop('ClimateVariables', None)

        self.capture_pump_cost_dollar_per_ML = kwargs.pop('capture_pump_cost_dollar_per_ML', self.calcCapturePumpCost())

        #Set default params
        self.default_params = {}
        for key, value in self.__dict__.iteritems():
            self.default_params[key] = value
        #End For

        self.default_waterstores = {}
        for key, value in self.WaterSources.__dict__.iteritems():
            self.default_waterstores[key] = value
        #End for

        self.default_climatevariables = {}
        for key, value in self.ClimateVariables.__dict__.iteritems():
            self.default_climatevariables[key] = value
        #End for

    #End init()

    def resetParams(self):
        for key, value in self.default_params.iteritems():
            setattr(self, key, value)
        #End for

        for key, value in self.default_waterstores.iteritems():
            setattr(self.WaterSources, key, value)
        #End for

        for key, value in self.default_climatevariables.iteritems():
            setattr(self.ClimateVariables, key, value)
        #End for

    #End resetParams()

    def loadParams(self, new_params):

        for key, value in new_params.items():

            if key is not 'surface_evap_rate' and key is not 'WaterSources' and key is not 'ClimateVariables':
                setattr(self, key, value)
            elif key is 'ClimateVariables':
                setattr(self, key, value)
            elif key is 'surface_evap_rate':
                setattr(self.ClimateVariables, key, value)
            elif key is 'WaterSources':
                setattr(self.WaterSources, key, value)
            #end if
        #End for
    #End loadParams()

    def calcNetWaterAvailable(self):

        """
        Stub. Define separately for each water store
        """
        pass

    #End calcNetWaterAvailable()

    def calcCapturePumpCost(self):

        self.capture_pump_cost_dollar_per_ML = self.pump_cost_dollar_per_ML * self.capture_pump_cost_ratio

        return self.capture_pump_cost_dollar_per_ML

    #End calcCapturePumpCost

    def calcSurfacePumpCost(self, total_surface_water):

        """
        Calculate how much it would cost to harvest water
        """

        surface_pump_cost = total_surface_water * self.calcCapturePumpCost()

        return surface_pump_cost

    #End calcSurfacePumpCost()

    def calcStorageCosts(self, water_to_store_ML):

        storage_cost = self.storage_cost_per_ML * water_to_store_ML

        return storage_cost

    #End calcStorageCosts()

    def calcPumpCost(self, water_volume_ML):

        """
        Calculate cost of pumping ML of water
        """

        pump_cost = water_volume_ML * self.pump_cost_dollar_per_ML

        return pump_cost

    #End calcPumpCost()

    def calcStorageCapitalCostPerML(self):

        #Referred to as [storage type].capital.cost in original code
        storage_capital_cost = self.cost_capital_per_ML * self.storage_capacity_ML

        return storage_capital_cost
    #End calcStorageCapitalCostPerML()

    def calcTotalCapitalCosts(self):

        capital_cost = self.calcDesignCosts() + self.calcStorageCapitalCostPerML() + self.cost_treatment_capital_cost + self.calcTemporaryStorageCosts()

        return capital_cost

    #End calcCapitalCosts()

    def calcDesignCosts(self):

        design_cost = self.calcCapitalCosts() * self.cost_of_design_as_proportion_of_capital

        return design_cost
    #End calcDesignCosts()

    def calcMaintenanceCosts(self, stored_water):
        maintenance_cost = self.maintenance_rate * self.calcStorageCosts(stored_water)

        return maintenance_cost
    #End calcMaintenanceCosts()

    def calcOngoingCosts(self):

        #Stub, to be defined in child classes
        #ongoing_costs = basin.maintenance.rate * basin.capital.cost.per.ml * asr.capacity.ml + surface.pump.cost + pump.vol.ml * pump.cost.dollar.per.ml
        pass
    #End calcCapitalCosts()

    def calcAnnualCosts(self):
        #Stub, to be defined in child classes
        pass
    #end calcAnnualCosts()


#End WaterStoragePractice()
