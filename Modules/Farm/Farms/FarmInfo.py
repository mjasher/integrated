from __future__ import division
import math
import copy

from integrated.Modules.Farm.Farms.FarmComponent import FarmComponent

class FarmInfo(FarmComponent):

    def __init__(self, name, storages, irrigations, crops, water_sources, max_irrigation_area_Ha=None, fields=None, discount_rate=None, **kwargs): #discount_rate=0.07

        """
        storages     : Dict of storage objects representing storages that is available for use
        crops        : Dict of Crop objects representing crops that could be produced by the farm
        irrigations  : Dict of irrigation objects that could be adopted
        """

        self.storages = storages
        self.irrigations = irrigations
        self.crops = crops
        self.max_irrigation_area_Ha = max_irrigation_area_Ha if max_irrigation_area_Ha is not None else 782.0
        self.name = name

        self.discount_rate = discount_rate
        self.water_sources = water_sources

        self.fields = fields if fields is not None else []

        self.net_profit = 0

        #Set all other kwargs as class attributes
        for key, value in kwargs.items():
            setattr(self, key, copy.deepcopy(value))
        #End For

    #End init()

    def resetParams(self):

        #Reset parameters for each store
        for store in self.storages:
            self.storages[store].resetParams()
        #End for

        for irrig in self.irrigations:
            self.irrigations[irrig].resetParams()

        for crop in self.crops:
            self.crops[crop].resetParams()

    #End resetParams()

    def calcValueAtX(self, x, set_param_set, comp_param_set):

        """
        Calculate the farm result when a variable is set to a specified value 'x'

        :param x: value for variable
        :param set_param_set: Values for other parameters at 'x'
        :param comp_param_set: Values to use for comparison
        :returns: Farm result when variable is set to 'x'
        """

        setting_method = set_param_set['method_name']
        comp_method = comp_param_set['method_name']
        set_params = set_param_set['params']
        comp_params = comp_param_set['params']

        set_params['amount'] = x

        try:
            #Set x value
            getattr(self, setting_method)(**set_params)
        except:
            print "Could not set value"
            return float("NaN")

        #calculate y-axis value at root_x (brentq sets root_x value)
        y = getattr(self, comp_method)(**comp_params)

        #Reset values back to default
        self.resetParams()

        return y
    #End calcValueAtX()

    def updateDiscountRate(self):
        #Hacky I know: Update discount rate in case it has changed
        self.discount_rate = self.storages[self.storages.keys()[0]].discount_rate
    #End if

    def setIrrigationEfficiency(self, irrigation_name=None, amount=None):

        """
        Defunct method, replace any use of this with setParam()

        :param irrigation_name: Name of irrigation method
        :param amount: efficiency of irrigation method, 0 to 1
        :returns: original value so that efficiency can be set back to 'normal' if necessary

        """

        irrigation_name = self.irrigations.keys()[0] if irrigation_name is None else irrigation_name

        original_value = self.irrigations[irrigation_name].irrigation_efficiency

        if amount is not None:
            self.irrigations[irrigation_name].irrigation_efficiency = amount
        #End if

        return original_value

    #End setIrrigationEfficiency()

    def getIrrigationEfficiency(self, irrigation_name=None):

        """
        Deprecated method, replace any use of this with getParam()
        """

        irrigation_name = self.irrigations.keys()[0] if irrigation_name is None else irrigation_name

        return self.irrigations[irrigation_name].irrigation_efficiency
    #End getIrrigationEfficiency()

    def getStorageInUse(self):
        for storage_name, Storage in self.storages.iteritems():
            if Storage.implemented == True:
                break
            #End if
        #End for

        return storage_name, Storage
    #End getStorageInUse()

    def getFarmArea(self):
        total = 0.0
        for f in self.fields:
            total = total + f.area
        #End for

        return total
    #End getFarmArea()

    def calcNetWaterAvailable(self):

        """
        Sums all the available water in all the water stores on the farm AFTER losses
        """

        water = 0
        for store in self.storages:
            water = water + self.storages[store].calcNetWaterAvailable()
        #End for

        return water

    #End calcNetWaterAvailable()

    def getNetWaterInWaterStore(self, store_name):

        try:
            water = self.storages[store_name].calcNetWaterAvailable()
        except KeyError:
            return 0

        return water

    #End getWaterInWaterStore()


    def calcNetStorageCost(self):

        storage_cost = 0
        for store in self.storages:
            storage_cost = storage_cost + self.storages[store].calcAnnualCosts()
        #End for

        return storage_cost

    #End calcNetStorageCost()

    def calcReqWaterApplicationMLperHa(self, crop_name):

        """
        Calculate required amount of water to be applied in ML per Ha
        NOTE: This is calculated for each irrigation strategy

        :return type: Dict
        """

        target_crop = self.crops[crop_name]

        water_applied = {}
        for irrigation_name in self.irrigations:

            water_applied[irrigation_name] = self.irrigations[irrigation_name].calcWaterAppliedMLperHa(target_crop.water_use_ML_per_Ha)
        #End for

        return water_applied

    #End calcReqWaterApplicationMLperHa()

    def calcFarmIrrigationArea(self, water_applied_ML_per_Ha, available_water_ML):

        """
        Calculate irrigation area for a single crop, capped to max irrigation area
        """

        irrigation_area = (available_water_ML / water_applied_ML_per_Ha)

        if(irrigation_area > self.max_irrigation_area_Ha):
            irrigation_area = self.max_irrigation_area_Ha
        #End if

        return irrigation_area

    #End calcFarmIrrigationArea()

    def calcIrrigationAreas(self, crop_name=None, net_available_water=None, irrigation_name=None):

        """
        Determines how much land can be irrigated if only one crop type is grown
        If amount of water is not specified, uses all available water
        """

        #self.calcNetWaterAvailable()
        if net_available_water is None:
            net_available_water = self.calcNetWaterAvailable()
        #End if

        irrigation_area = {}
        if crop_name is not None and irrigation_name is not None:

            water_applied = self.calcReqWaterApplicationMLperHa(crop_name=crop_name)

            #irrigation_area[crop_name] = {}
            irrigation_area = self.calcFarmIrrigationArea(water_applied[irrigation_name], net_available_water)

            return irrigation_area

        #End if

        for crop_name in self.crops:

            water_applied = self.calcReqWaterApplicationMLperHa(crop_name=crop_name)

            irrigation_area[crop_name] = {}

            for irrigation_name in self.irrigations:
                irrigation_area[crop_name][irrigation_name] = self.calcFarmIrrigationArea(water_applied[irrigation_name], net_available_water)
            #End for

        #End for

        return irrigation_area

    #End calcIrrigationAreas()

    def calcIrrigationCapitalCosts(self, irrigation_area, irrigation_name):

        self.updateDiscountRate()

        return self.irrigations[irrigation_name].calcAnnualCapitalCost(irrigation_area, self.discount_rate)

    #End calcIrrigationCapitalCosts()

    def calcFarmOverheadCost(self):

        return 0

    #End calcFarmOverheadCost()

    def calcTotalFarmGrossMarginPerHa(self, land_use_Ha):

        """
        Calculate the total amount of money generated by irrigation per Ha
        """

        gross_value_per_yield = 0
        for crop_name in self.crops:
            gross_value_per_yield = gross_value_per_yield + self.crops[crop_name].calcTotalCropGrossMargin(land_use_Ha)
        #End for

        return (gross_value_per_yield / land_use_Ha)

    #End calcTotalFarmGrossMarginPerHa

    def calcTotalFarmGrossMargins(self, land_use_Ha):

        """
        Calculate total farm gross margin
        """

        gross_value = 0
        for crop_name in self.crops:
            gross_value = gross_value + self.crops[crop_name].calcTotalCropGrossMargin(land_use_Ha)
        #End for

        return gross_value

    #End calcTotalFarmGrossMargins()

    def calcNetFarmIncome(self, irrigation_area=None, irrigation_name=None, crop_name='Cotton'):

        """
        Calculate net income by calculating total gross margin then subtract capital costs
        """

        if irrigation_name is None:
            irrigation_name = self.irrigations.keys()[0]
            #raise ValueError('Name of irrigation system to calculate income from was not given')
        #End if

        if(irrigation_area is None):
            irrigation_area = self.calcIrrigationAreas(crop_name)
            irrigation_area = irrigation_area[crop_name][irrigation_name]
        #End if

        return self.calcTotalFarmGrossMargins(irrigation_area) - self.calcTotalCapitalCosts(irrigation_name, irrigation_area)

    #End calcNetFarmIncome()

    def calcAnnualizedNetIncome(self, irrigation_area=None, irrigation_name=None, crop_name='Cotton'):

        """
        Calculate Annualised Net Income
          annualized_income = (gross_income - implementation_cost) * ((1 + self.discount_rate)**(-max_life) - 1)/(-self.discount_rate)

        """

        if irrigation_name is None:
            irrigation_name = self.irrigations.keys()[0]
            #raise ValueError('Name of irrigation system to calculate income from was not given')
        #End if

        if(irrigation_area is None):
            irrigation_area = self.calcIrrigationAreas(crop_name)
            irrigation_area = irrigation_area[crop_name][irrigation_name]
        #End if

        store_name = self.storages.keys()[0]
        irrigation_name = self.irrigations.keys()[0]

        store_life = self.getParam(component='storages', comp_name=store_name, attr_name='num_years')
        irrig_life = self.getParam(component='irrigations', comp_name=irrigation_name, attr_name='lifespan')

        max_life = max(store_life, irrig_life)
        min_life = min(store_life, irrig_life)

        gross_income = self.calcTotalFarmGrossMargins(irrigation_area)

        implementation_cost = self.calcAnnualizedCosts(store_name, irrigation_name, irrigation_area)

        #Hacky I know: Update discount rate in case it has changed
        self.updateDiscountRate()

        #From original code
        #annual.cash.flow * ((1 + discount.rate)^(-nyears) - 1)/(-discount.rate)
        annualized_income = (gross_income - implementation_cost) * ((1 + self.discount_rate)**(-max_life) - 1)/(-self.discount_rate)

        return annualized_income

    #End calcAnnualIncome()

    def calcAnnualizedCosts(self, store_name, irrigation_name, irrig_area):

        """
        Calculate Annualised implementation costs
        """

        import Common.GeneralFunctions as GeneralFunctions

        #Annualise gross income using the greatest lifespan

        store_life = self.getParam(component='storages', comp_name=store_name, attr_name='num_years')
        irrig_life = self.getParam(component='irrigations', comp_name=irrigation_name, attr_name='lifespan')

        max_life = max(store_life, irrig_life)
        min_life = min(store_life, irrig_life)

        #Hacky I know: Update discount rate in case it has changed
        self.updateDiscountRate()

        #get non-annualised cost of replacing irrigation
        irrig_cost = self.irrigations[irrigation_name].calcReplacementCost(irrig_area)

        #non-annualised cost of storage
        store_cost = self.storages[store_name].calcTotalCapitalCosts()

        if min_life == irrig_life:
            #proportion of non-annualised cost of irrigation
            part_cost = irrig_cost * math.ceil(max_life / min_life)
        else:
            #proportion of non-annualised cost of storage
            part_cost = store_cost * math.ceil(max_life / min_life)
        #End if

        implementation_cost = store_cost + irrig_cost + part_cost
        implementation_cost = GeneralFunctions.calcCapitalCostPerYear(implementation_cost, self.discount_rate, max_life) + self.storages[store_name].calcOngoingCosts()

        return implementation_cost

    #End calcAnnyalizedCosts()

    def calcTotalCapitalCosts(self, irrigation_name, irrigation_area):

        """
        Calculate total capital costs of farm
        """

        return (self.calcNetStorageCost() + self.calcIrrigationCapitalCosts(irrigation_area, irrigation_name))

    #End calcTotalCapitalCosts()

    def calcTotalCropYield(self, crop_name='Cotton', irrigation_area=None, irrigation_name=None):

        if irrigation_name is None:
            irrigation_name = self.irrigations.keys()[0]
        #End if

        if irrigation_area is None:
            irrigation_area = self.calcIrrigationAreas(crop_name=crop_name, irrigation_name=irrigation_name)
        #End if

        return self.crops[crop_name].yield_per_Ha * irrigation_area


    def calcGPWUI(self, crop_name='Cotton', crop_yield=None, irrigation=None):

        """
        Calculate Gross Production Water Use Index
        GPWUI = yield / total water at start of scenario (before losses etc)
        Returns Bale/ML
        """

        if irrigation is None:
            #Use first irrigation system if not specified
            irrigation = self.irrigations.keys()[0]
        #End if

        if crop_yield is None:
            crop_yield = self.calcTotalCropYield(crop_name=crop_name, irrigation_name=irrigation)
        #End if

        total_water = self.calcTotalWaterInput()

        return crop_yield / total_water

    #End

    def calcIWUI(self, crop_name='Cotton', crop_yield=None, irrigation_water=None):
        """
        Calculate Irrigation Water Use Index
        IWUI = yield / water used for irrigation
        Returns Bale/ML
        """

        if crop_yield is None:
            crop_yield = self.calcTotalCropYield(crop_name=crop_name)
        #End if

        if irrigation_water is None:
            irrigation_water = self.calcNetWaterAvailable()
        #End if

        return crop_yield / irrigation_water
    #End calcIWUI

    def calcTotalWaterInput(self):

        water = 0
        for store in self.storages:
            water = water + self.storages[store].WaterSources.calcGrossWaterAvailable()
        #End for

        return water
    #End calcTotalWaterInput()

    def applyCropLosses(self):

        for f in self.fields:
            f.applyCropLoss()
        #End for
    #End applyCropLosses
