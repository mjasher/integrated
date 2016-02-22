from __future__ import division
import copy
import pandas as pd
from datetime import datetime

from integrated.Modules.Core.IntegratedModelComponent import Component

class CropInfo(Component):

    """
    Crop Object that represents a crop type
    """

    def __init__(self, crop_name, price_per_yield, variable_cost_per_Ha, yield_per_Ha=None, gross_margin_per_Ha=None, water_use_ML_per_Ha=None, required_water_ML_per_Ha=None, depletion_fraction=None, **kwargs):

        """
        crop_name                       : Human readable name of crop
        yield_per_Ha                    : Yield per Hectare (with "normal" base irrigation technique)
        price_per_yield                 : Expected price per yield (in tonnes or bales)
        variable_cost_per_Ha            : Variable cost per Hectare
        land_used_Ha                    : How much land is devoted to this crop type in Hectares
        water_use_ML_per_Ha             : Gross amount of water applied to the field in ML per Hectare (NOT HOW MUCH WATER IS REQUIRED BY THE CROP)
        required_water_ML_per_Ha        : Net amount of water is required by the crop in ML per Hectare
        water_need_distribution         : Dict of growth stages and crop coefficients {'stage name': {'length (in days)': 0, 'coefficient': 0.5}}

        root_depth_m                    : Root depth of plant
        planting_info                   : Growth stages and crop coefficient for that stage (see http://www.fao.org/docrep/x0490e/x0490e0b.htm)
        depletion_fraction              : Fraction of total available water (TAW) that can be depleted from the root zone before moisture stress occurs

        See:
        http://agriculture.vic.gov.au/agriculture/horticulture/vegetables/vegetable-growing-and-management/estimating-vegetable-crop-water-use
        especially table 4.
        
        http://www.fao.org/docrep/x0490e/x0490e0b.htm

        """

        self.name = crop_name

        #self.yield_per_Ha = yield_per_Ha if yield_per_Ha is not None else 0.0
        self.setAttribute('yield_per_Ha', yield_per_Ha, 0.0)
        self.setAttribute('water_use_ML_per_Ha', water_use_ML_per_Ha, None)
        self.setAttribute('required_water_ML_per_Ha', required_water_ML_per_Ha, None)
        self.setAttribute('depletion_fraction', depletion_fraction, 0.4)
        
        self.price_per_yield = price_per_yield
        self.variable_cost_per_Ha = variable_cost_per_Ha
        self.water_need_satisfied = 0.0
        self.planted = False

        #Set all other kwargs as class attributes
        for key, value in kwargs.items():
            setattr(self, key, copy.deepcopy(value))
        #End For

    #End init()

    def updateWaterNeedsSatisfied(self, water_use_ML, area_Ha):
        """
        Update water needs for this crop
        
        :param water_use_ML: represents in ML the ET of this crop for the given area
        :param area: total area in Hectares for this crop

        """
        try:
            self.water_need_satisfied = (water_use_ML / area_Ha) / self.required_water_ML_per_Ha
        except ZeroDivisionError as e:
            self.water_need_satisfied = 1
        #End try

    #End updateWaterNeedsSatisfied()

    def getCurrentStageCoef(self, timestep):

        """
        Get crop coefficient for current stage of crop development as indicated by the timestep
        TODO: Not sure if this method will be used

        :param timestep: Date Object representing current timestep
        :returns: Coefficient for the development stage of plant
        """

        year = timestep.year

        temp_df = self.planting_info.copy()

        #Prepend year to each crop coefficient entry
        temp_df['temp_dt'] = "{y}-".format(y=year)+temp_df['Month-Day'].astype(str)

        coef = temp_df[(pd.to_datetime(temp_df['temp_dt']) <= timestep)]['Coefficient']

        if len(coef) == 0:
            return 0.0
        
        #Return the coefficient for the given timestep
        return temp_df[(pd.to_datetime(temp_df['temp_dt']) <= timestep)]['Coefficient'][0]
        
    #End getCurrentStageCoef()

    def harvest(self, timestep):
        temp_df = self.planting_info.copy()

        year = timestep.year

        #Prepend year to each crop coefficient entry
        temp_df['temp_dt'] = "{y}-".format(y=year)+temp_df['Month-Day'].astype(str)

        # harvest_time = pd.to_datetime(temp_df['temp_dt']['harvest'])
        harvest_time = pd.to_datetime(temp_df.loc['harvest', 'temp_dt']).date()

        print timestep
        print harvest_time

        if timestep >= harvest_time: #harvest_time.date():
            return True

        return False

    #End harvest

    def calcTotalCropGrossMarginsPerHa(self, yield_per_Ha=None, price_per_yield=None):

        """
        Calculate gross income from crop per Hectare

        :math:`Crop Yield * Crop Price`

        :param yield_per_Ha: Estimated or assumed crop yield per Ha. Defaults to assumed value.
        :param price_per_yield: Estimated or assumed crop price per unit (Tons/Bales/etc). Defaults to assumed value.

        :returns: total gross margins per Hectare based on the assumed or given crop yield and crop price


        """

        if yield_per_Ha is None:
            yield_per_Ha = self.yield_per_Ha

        if price_per_yield is None:
            price_per_yield = self.price_per_yield

        gross_margin_per_Ha = yield_per_Ha * price_per_yield

        return gross_margin_per_Ha

    #End calcTotalCropGrossMarginsPerHa()

    def calcGrossMarginsPerHa(self, yield_per_Ha=None, price_per_yield=None):

        """
        Calculate $/ML/Ha 
        :returns: Dollar value per MegaLitre, per Hectare
        """

        if yield_per_Ha is None:
            yield_per_Ha = self.yield_per_Ha

        if price_per_yield is None:
            price_per_yield = self.price_per_yield

        return (self.calcTotalCropGrossMarginsPerHa(yield_per_Ha, price_per_yield) / self.water_use_ML_per_Ha)

    #End calcGrossMarginsML()

    def calcTotalCropGrossMargin(self, land_used_Ha, yield_per_Ha, price_per_yield):

        """
        Calculate gross income from crop for a given irrigated area, taking into account variable costs
        :param land_used_Ha: Amount of land dedicated to this crop type
        """

        if yield_per_Ha is None:
            yield_per_Ha = self.yield_per_Ha

        if price_per_yield is None:
            price_per_yield = self.price_per_yield

        total_crop_gross_margin = land_used_Ha * self.calcTotalCropGrossMarginsPerHa(yield_per_Ha, price_per_yield)

        return total_crop_gross_margin

    #End calcTotalFarmGrossMargin()

#End class
