from integrated.Modules.Core.IntegratedModelComponent import Component

class WaterSources(Component):

    """
    Represents a source of water
    """

    def __init__(self, name, water_level, entitlement, water_value_per_ML, cost_per_ML, **kwargs):

        """
        :param name: Name of water source 
        :param water_level: Current water level
        :param entitlement: Amount of water entitled from this water source
        :param water_value_per_ML: Market value of the water
        :param cost_per_ML: Cost of ordering the water
        """

        self.name = name
        self.water_level = water_level
        self.entitlement = entitlement
        self.water_value_per_ML = water_value_per_ML
        self.cost_per_ML = cost_per_ML

        #Set all kwargs as class attributes
        for key, value in kwargs.items():
            setattr(self, key, value)
        #End For

    #End init()

    def calcGrossWaterAvailable(self):

        #return sum(self.water_source.values())
        return self.entitlement

    #End calcGrossWaterAvailable()

    def extractWater(self):
        pass
    #End extractWater()

    def calcPumpingCostsPerML(self, flow_rate_Lps, duration=24, pump_efficiency=0.7, derating=1, fuel_per_Kw=0.25):

        """
        :param flow_rate_Lps: required flow rate in Litres per second over the irrigation duration
        :param duration: Irrigation duration in hours, defaults to 24 hours
        :param pump_efficiency: Efficiency of pump. Defaults to 0.7 (70%)
        :param derating: Accounts for efficiency losses between the energy required at the pump shaft and the total energy required. Defaults to 1
        :param fuel_per_Kw: Amount of fuel required for a Kilowatt hour. Defaults to 0.25L for diesel.

        See 
          * `Robinson, D. W., 2002 <http://www.clw.csiro.au/publications/technical2002/tr20-02.pdf>`_
          * `Vic. Dept. Agriculture, 2006 <http://agriculture.vic.gov.au/agriculture/farm-management/soil-and-water/irrigation/border-check-irrigation-design>`_


        """

        constant = 102
        energy_required = (self.water_level * flow_rate_Lps) / ((constant * pump_efficiency) * derating)

        fuel_required_per_Hour = energy_required * fuel_per_Kw

        hours_per_ML = 24 / flow_rate_Lps

        cost_per_ML = fuel_required_per_Hour * hours_per_ML

        return cost_per_ML

    #End calcPumpingCostsPerML()

    def calcGrossPumpingCostsPerHa(self, flow_rate_Lps, est_irrigation_water_ML_per_Ha, duration=24, pump_efficiency=0.7, derating=1, fuel_per_Kw=0.25):
        pumping_cost_per_Ha = self.calcPumpingCostsPerML(flow_rate_Lps, duration, pump_efficiency, derating, fuel_per_Kw) * est_irrigation_water_ML_per_Ha

        return pumping_cost_per_Ha
    #End calcGrossPumpingCosts()

    def calcWaterCostsPerHa(self, water_amount_ML_per_Ha):
        return self.cost_per_ML * water_amount_ML_per_Ha
    #End calcWaterCostsPerHa()

        

#End WaterSources
