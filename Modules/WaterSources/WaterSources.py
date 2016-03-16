from integrated.Modules.Farm.Farms.FarmComponent import FarmComponent
import numpy as np

class WaterSources(FarmComponent):

    """
    Represents a source of water
    """

    def __init__(self, name, water_level, entitlement, water_value_per_ML, cost_per_ML, **kwargs):

        """
        :param name: Name of water source 
        :param water_level: Current water level, depth below ground level
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

    def calcPumpingCostsPerML(self, flow_rate_Lps, head_pressure=None, additional_head=0.0, pump_efficiency=0.7, derating=0.75, fuel_per_Kw=0.25, fuel_price_per_Litre=1.25):

        """
        :param flow_rate_Lps: required flow rate in Litres per second over the irrigation duration
        :param head_pressure: Head pressure of pumping system in metres. Uses water level of water source if not given.
        :param additional_head: Additional head pressure, typically factored in from the implemented irrigation system
        :param pump_efficiency: Efficiency of pump. Defaults to 0.7 (70%)
        :param derating: Accounts for efficiency losses between the energy required at the pump shaft and the total energy required. Defaults to 1
        :param fuel_per_Kw: Amount of fuel (in litres) required for a Kilowatt hour. Defaults to 0.25L for diesel.
        :param fuel_price_per_Litre: Price of fuel per Litre, defaults to 1.25

        See 
          * `Robinson, D. W., 2002 <http://www.clw.csiro.au/publications/technical2002/tr20-02.pdf>`_
          * `Vic. Dept. Agriculture, 2006 <http://agriculture.vic.gov.au/agriculture/farm-management/soil-and-water/irrigation/border-check-irrigation-design>`_
          * `Vellotti & Kalogernis, 2013 <http://irrigation.org.au/wp-content/uploads/2013/06/Gennaro-Velloti-and-Kosi-Kalogernis-presentation.pdf>`_

        .. :math:
            P(Kw) = (H * Q) / ((102 * Ep) * D)

        where:
        * :math:`H` is head pressure in metres (m)
        * :math:`Q` is Flow in Litres per Second
        * :math:`Ep` is Pump efficiency (defaults to 0.7)
        * :math:`D` is the derating factor
        * :math:`102` is a constant, as given in Velloti & Kalogernis (2013)
        """

        if flow_rate_Lps <= 0:
            return 0.0

        if head_pressure is None:
            head_pressure = self.water_level

        head_pressure = head_pressure + additional_head

        constant = 102
        energy_required_Kw = (head_pressure * flow_rate_Lps) / ((constant * pump_efficiency) * derating)

        fuel_required_per_Hour = energy_required_Kw * fuel_per_Kw

        hours_per_ML = (1000000 / flow_rate_Lps) / 60 / 60 #Litres / minutes in hour / seconds in minute

        cost_per_ML = (fuel_price_per_Litre * fuel_required_per_Hour) * hours_per_ML

        # print "---- Pumping Cost Calculation ----"
        # print "Head pressure: {h}".format(h=head_pressure)
        # print "Water Level: {wl}".format(wl=self.water_level)
        # print "Given flow rate: {f}".format(f=flow_rate_Lps)
        # print "Energy Kw: {kw}".format(kw=energy_required_Kw)
        # print "Fuel / Hour: {f}".format(f=fuel_required_per_Hour)
        # print "Hours / ML: {f}".format(f=hours_per_ML)
        # print "Cost per ML: {f}".format(f=cost_per_ML)
        # print "=================================="

        return cost_per_ML

    #End calcPumpingCostsPerML()

    def calcGrossPumpingCostsPerHa(self, flow_rate_Lps, est_irrigation_water_ML_per_Ha, head_pressure=None, additional_head=0.0, pump_efficiency=0.7, derating=0.75, fuel_per_Kw=0.25):
        pumping_cost_per_Ha = self.calcPumpingCostsPerML(flow_rate_Lps, head_pressure, additional_head, pump_efficiency, derating, fuel_per_Kw) * est_irrigation_water_ML_per_Ha

        return pumping_cost_per_Ha
    #End calcGrossPumpingCostsPerHa()

    def calcCapitalCosts(self):

        pass
    #End calcCapitalCosts()


    def calcWaterCostsPerHa(self, water_amount_ML_per_Ha):
        return self.cost_per_ML * water_amount_ML_per_Ha
    #End calcWaterCostsPerHa()

    def calcTotalCostsPerHa(self, water_amount_ML_per_Ha):
        return self.cost_per_ML * water_amount_ML_per_Ha
    #End calcTotalCostsPerHa()

        

#End WaterSources
