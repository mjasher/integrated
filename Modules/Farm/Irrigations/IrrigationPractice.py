from Modules.Core.IntegratedModelComponent import Component
from Modules.Core.GeneralFunctions import *

class IrrigationPractice(Component):

    """
    Represents an irrigation practice/technology.

    Methods defined in this parent class should be considered stubs, to be redefined by child Classes.
    """

    def __init__(self, name, irrigation_efficiency, cost_per_Ha, replacement_cost_per_Ha=None, irrigation_rate=None, lifespan=None, max_irrigation_area_Ha=None): #discount_rate=0.07

        self.name = name

        self.irrigation_rate = 1 if irrigation_rate is None else irrigation_rate
        self.irrigation_efficiency = irrigation_efficiency

        #Cost of replacing the irrigation system after lifespan.
        self.replacement_cost_per_Ha = cost_per_Ha if replacement_cost_per_Ha is None else replacement_cost_per_Ha

        #Implementation cost for Flood is always 0 as it is already implemented
        self.cost_per_Ha = cost_per_Ha if name is not 'Flood' else 0.0
        
        #max irrigation area default value (782 Ha) from Powell & Scott (2011), Representative farm model, p 25
        self.max_irrigation_area_Ha = max_irrigation_area_Ha if max_irrigation_area_Ha is not None else 782.0
        self.lifespan = lifespan if lifespan is not None else 10
        #self.discount_rate = discount_rate

        #self.irrigation_area = 0.0 if irrigation_area is None else irrigation_area

        #Set default params
        self.default_params = {}
        for key, value in self.__dict__.iteritems():
            self.default_params[key] = value
        #End For

    #End init()

    def resetParams(self):
        for key, value in self.default_params.iteritems():
            setattr(self, key, value)
        #End for
    #End resetParams()

    def calcCropWaterRequirement(self, applied_ML_per_Ha):

        """
        Calculate how much water is required for a given crop, determined from the base applied water

        applied_ML_per_Ha: Water applied for crop MegaLitres per Ha under flood irrigation

        This is different from Water Applied.

        Water Applied is the amount of water sent out to the field

        Crop Water Requirement is the amount of water actually used by the crop.
        """

        return applied_ML_per_Ha - self.calcIrrigationEfficiencySaving(applied_ML_per_Ha)

    #End calcWaterRequirement

    def calcIrrigationEfficiencySaving(self, crop_water_req_ML_per_Ha):

        """
        Calculate the amount of water saved per Hectare due to efficiency increase
        """

        return (crop_water_req_ML_per_Ha * (1 - self.irrigation_efficiency))

    #End calcIrrigationEfficiencySaving()

    def calcIrrigationEfficiency(self, crop_water_req_ML_per_Ha):

        """
        In this model, irrigation efficiency is an assumed/known value.
        With breakeven analysis we vary this value to determine a point of concern.
        This method is a stub which should be overwritten by implementing Classes.

        In the interest of context:

        Percentage of water delivered to the field that is used beneficially (Irrigation Efficiency - :math:`E_{i}`) can be calculated as

          :math:`E_{i} = 100(W_{b} / W_{f})`, where :math:`W_{b}` is Water used beneficially, and :math:`W_{f}` is water delivered to field

          Rogers et al. (1997)

        :param crop_water_req_ML_per_Ha: Amount of water in ML per Ha applied to the field.
        :type crop_water_req_ML_per_Ha: float, ML per Hectare
        :returns: percent (e.g. 76 percent = 0.76 * 100 = 76)
        :return type: numeric

        """

        #( (crop_water_req_ML_per_Ha * self.irrigation_efficiency) / crop_water_req_ML_per_Ha)
        # Should be : 100 * (water used by plant / water sent to field)

        pass

        #irrigation_efficiency = 100 * self.irrigation_efficiency

        #return irrigation_efficiency

    #End calcIrrigationEfficiency()

    def calcWaterApplicationEfficiency(self, water_delivered_to_field):

        """
        Context:
        Rogers et al. (1997)

        Percentage of water delivered to the field used by the crop
          :math:`E_{a} = 100(W_{c} / W_{f})`, where :math:`E_{a}` is Water Application Efficiency

          :math:`W_{c}` is water available for use by the crop

          :math:`W_{f}` is the water delivered to the field

        :param water_delivered_to_field: Amount of water (in ML) applied to the field
        :type water_delivered_to_field: numeric, MegaLitres
        :returns: percentage (e.g. 0.76 = 76 percent = 76)
        :return type: numeric

        """

        water_for_crop = water_delivered_to_field * self.irrigation_efficiency

        water_app_efficiency = 100 * (water_for_crop / water_delivered_to_field)

        return water_app_efficiency

    #End calcWaterApplicationEfficiency()

    def calcWaterSavings(self, irrigation_area, crop_water_req_ML_per_Ha, efficiency=None):

        """
        Calculates water savings

        :math:`Water Saved = Irrigation Area * Crop Water Requirement In ML per Ha * Irrigation Efficiency`

        :returns: water saved in ML
        :return type: numeric
        """

        efficiency = self.irrigation_efficiency if efficiency is None else efficiency

        saved_water = irrigation_area * (crop_water_req_ML_per_Ha * (1 - efficiency))

        return saved_water

    #End calcWaterSavings

    def calcWaterAppliedMLperHa(self, base_application_ML_per_Ha):

        """
        WARNING: DEPRECATED, DO NOT USE

        Calculate how much water needs to be applied in MegaLitres per Hectare

        Based on given required amount of water for a given crop

        This is different from Crop Water Requirement.

        Water Applied is the amount of water sent out to the field to satisfy crop water requirements

        Crop Water Requirement is the amount of water actually needed by the crop

        :param base_application_ML_per_Ha: Suggested application amount for given crop type
        :returns: adjusted amount of water to apply
        :return type: numeric

        """

        return ((base_application_ML_per_Ha / (self.irrigation_efficiency * 100)) * 100) * self.irrigation_rate

    #End calcWaterAppliedMLperHa

    def calcIrrigationArea(self, water_applied_ML_per_Ha, available_water_ML):

        """
        Calculate irrigation area, capped to max irrigation area

        :param water_applied_ML_per_Ha: Amount of water applied in ML per Hectare
        :param available_water_ML: Amount of water currently available
        :returns: Area (in Hectares) that can be irrigated, constrained by maximum irrigation area
        :return type: numeric
        """

        irrigation_area = (available_water_ML / water_applied_ML_per_Ha)

        if(irrigation_area > self.max_irrigation_area_Ha):
            irrigation_area = self.max_irrigation_area_Ha

        return irrigation_area

    #End calcIrrigationArea()

    def calcCapitalCost(self, irrigation_area_Ha):

        """
        Calculate the implementation cost of this irrigation practice

        :param irrigation_area_Ha: Area under irrigation in Hectares
        :returns: Capital cost of implementing irrigation practice/technology
        :return type: numeric
        """

        return irrigation_area_Ha * self.cost_per_Ha

    #End calcCapitalCost()

    def calcReplacementCost(self, irrigation_area_Ha):

        """
        Calculate the replacement cost for a given irrigation system.
          Replacement cost is assumed to be equal to the initial cost per Hectare.

        :param irrigation_area_Ha: Area of irrigation system
        :returns: replacement cost in dollar terms
        :return type: float
        """

        self.replacement_cost_per_Ha = self.replacement_cost_per_Ha if self.cost_per_Ha == 0 else self.cost_per_Ha

        return irrigation_area_Ha * self.replacement_cost_per_Ha
    #End calcReplacementCost()

    def calcOngoingCost(self):

        """
        Not included due to lack of information
          See Powell & Scott 2011 (p 42) for overhead costs
        
        """

        return 0
    #End calcOngoingCost()

    def calcAnnualCapitalCost(self, irrigation_area_Ha, discount_rate):

        """
        Calculates Capital Cost of irrigation system on a per year basis, discounted to present day value

        :param irrigation_area_Ha: Area under irrigation in Hectares
        :param discount_rate: Percentage to discount future value to get present day value
        :returns: annualised NPV ($)
        :return type: numeric
        """

        capital_cost = self.calcCapitalCost(irrigation_area_Ha)
        ongoing_cost = self.calcOngoingCost()

        return calcCapitalCostPerYear(capital_cost, discount_rate, self.lifespan) + ongoing_cost

    #End calcAnnualCost()

#End IrrigationPractice()
