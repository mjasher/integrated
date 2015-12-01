from __future__ import division
import copy
from integrated.Modules.Core.IntegratedModelComponent import Component

class CropInfo(Component):

    """
    Crop Object that represents a crop type
    """

    def __init__(self, crop_name, price_per_yield, variable_cost_per_Ha, yield_per_Ha=None, gross_margin_per_Ha=None, water_use_ML_per_Ha=None, required_water_ML_per_Ha=None, **kwargs):

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
        growth_stages                   : Length of growth stages in days (see http://www.fao.org/docrep/x0490e/x0490e0b.htm)
        growth_water_requirements       : Required water for each growth stage

        sow_time                        : Month when to sow
        harvest_time                    : Month when to start harvest

        See:
        http://agriculture.vic.gov.au/agriculture/horticulture/vegetables/vegetable-growing-and-management/estimating-vegetable-crop-water-use
        especially table 4.
        
        http://www.fao.org/docrep/x0490e/x0490e0b.htm

        """

        self.name = crop_name
        self.yield_per_Ha = yield_per_Ha if yield_per_Ha is not None else 0.0
        self.price_per_yield = price_per_yield
        self.variable_cost_per_Ha = variable_cost_per_Ha
        self.water_use_ML_per_Ha = water_use_ML_per_Ha if water_use_ML_per_Ha is not None else None
        self.required_water_ML_per_Ha = required_water_ML_per_Ha if required_water_ML_per_Ha is not None else None
        self.water_need_satisfied = 0.0
        self.planted = False

        #Set all other kwargs as class attributes
        for key, value in kwargs.items():
            setattr(self, key, copy.deepcopy(value))
        #End For

        #Set default params
        # self.default_params = {}
        # for key, value in self.__dict__.iteritems():
        #     self.default_params[key] = copy.deepcopy(value)
        # #End For

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

        from datetime import datetime

        year = timestep.year

        coef = 0.0
        for info in self.planting_info:
            stage_dt = '{y}-{md}'.format(y=year, md=self.planting_info[info][0])
            stage_dt = datetime.strptime(stage_dt, '%Y-%m-%d').date()

            if timestep < stage_dt:
                continue
            else:
                coef = self.planting_info[info][1]
            #End if

        #End for

        return coef
    #End getCurrentStageCoef()

    def calcTotalCropGrossMarginsPerHa(self):

        """
        Calculate total income from crop per Hectare, taking into account variable costs

        :returns: total gross margins per Hectare based on assumed yield per Ha, price per Yield, and variable costs per Hectare
        """

        gross_value_per_yield = self.yield_per_Ha * self.price_per_yield

        total_crop_gross_margin_per_Ha = gross_value_per_yield - self.variable_cost_per_Ha

        return total_crop_gross_margin_per_Ha

    #End calcTotalCropGrossMarginsPerHa()

    def calcGrossMarginsPerHa(self):

        """
        Calculate Gross Margins per Hectare ($/Ha)
        :returns: Dollar value per Hectare
        """

        return (self.calcTotalCropGrossMarginsPerHa() / self.water_use_ML_per_Ha)

    #End calcGrossMarginsML()

    def calcTotalCropGrossMargin(self, land_used_Ha):

        """
        Calculate gross income from crop for a given irrigated area, taking into account variable costs
        :param land_used_Ha: Amount of land dedicated to this crop type
        """

        total_crop_gross_margin = land_used_Ha * self.calcTotalCropGrossMarginsPerHa()

        return total_crop_gross_margin

    #End calcTotalFarmGrossMargin()

#End class
