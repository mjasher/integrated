from __future__ import division
import copy
import pandas as pd
import numpy as np
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

        #Count number of seasons it has been in rotation
        self.rotation_count = 0


        # self.plant_date = plant_date #Estimated season start

        #also set, but not here
        #season_info

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

    def _preparePlantingInfo(self, timestep):

        """
        Modifies planting dataframe for queries
        """

        year = timestep.year

        temp_df = self.planting_info.copy()

        #Prepend year to each crop coefficient entry
        temp_df['temp_dt'] = "{y}-".format(y=year)+temp_df['Month-Day'].astype(str)

        return temp_df
    #End _preparePlantingInfo()

    def _prepareSeasonInfo(self, val_type="Best Guess"):

        temp_df = self.season_info.copy()

        #Remove all non-numeric columns
        temp_df = temp_df.select_dtypes(include=['float64', 'int64'])

        assert len(temp_df) > 0, "No seasonal crop growth information found"

        #Cumulatively sum all rows
        temp_df = temp_df.cumsum(axis=1)

        temp_df['plant_date'] = self.season_info.loc[:, 'plant_date']

        return temp_df
    #End _prepareSeasonInfo()

    def _getPreparedSeasonInfo(self, val_type):
        try:
            season_info = self.prepped_season_info
        except AttributeError:
            season_info = self._prepareSeasonInfo(val_type)
            self.prepped_season_info = season_info
        #End try

        return season_info.loc[val_type, :].copy()
    #End getPreparedSeasonInfo()

    def getCurrentStage(self, timestep, val_type="Best Guess"):

        season_info = self._getPreparedSeasonInfo(val_type)
        season_info = season_info.drop('plant_date')

        days_from_season_start = ((pd.to_datetime(timestep) - self.plant_date) / np.timedelta64(1, 'D')).astype(int)

        temp = ([days_from_season_start, ] * len(season_info)) <= season_info

        try:
            stage = temp[temp == True].index[0].lower()
        except IndexError:
            #Gone past seasonal growth stages, (past 'late'/'harvest' date)
            stage = temp.index[-1].lower()

        return stage
    #End getCurrentStage()

    def getStageCoef(self, timestep, coef_name, val_type="Best Guess"):

        stage = self.getCurrentStage(timestep, val_type)

        pi = self.planting_info
        coef = pi.loc[pi.index.str.lower() == stage, coef_name]

        assert len(coef) > 0, "Plant coefficient not found"

        return coef.iloc[0]
    #End getStageCoef()

    def getCurrentStageDepletionCoef(self, timestep, val_type="Best Guess"):

        """
        Get Plant Depletion Coefficient for current stage
        """

        assert self.plant_date != None, "Plant date not set!"

        return self.getStageCoef(timestep, "Depletion Fraction", val_type)
    #End getCurrentStageDepletionCoef()

    def getCurrentStageCropCoef(self, timestep, val_type="Best Guess"):
        """
        Get current stage crop coefficient (:math:`Kc`)
        """
        return self.getStageCoef(timestep, "Crop Coefficient", val_type)
    #End getCurrentStageCropCoef()

    # def getCurrentStageRootDepth(self, timestep, val_type="Best Guess"):
    #     return self.getStageCoef(timestep, "Root Depth", val_type)
    # #End getCurrentStageRootDepth()

    def getSeasonStart(self, timestep):

        # temp_df = self._preparePlantingInfo(timestep)
        # #Return datetime of season start
        # return temp_df.iloc[0]['temp_dt']

        return "{y}-{md}".format(y=timestep.year, md=self.plant_date)

    #End getSeasonStart()

    def getSeasonStartRange(self, timestep, step, val_type='Best Guess', format='%Y-%m-%d'):

        """
        Gets the season start date and the next timestep datetime for a crop.
        Essentially returns the step range in which the crop might be planted.
        e.g. If time step is 7 days and plant date is May 15, then the crop season might be planted between
            May 15 and May 22
        """

        season_info = self._getPreparedSeasonInfo(val_type)

        start = "{y}-{md}".format(y=timestep.year, md=season_info["plant_date"])
        end = pd.to_datetime(datetime.strptime(start, format) + pd.Timedelta(days=step))

        return start, end
    #End getSeasonStartRange

    def getSeasonStartEnd(self, timestep, val_type="Best Guess"):

        season_info = self._getPreparedSeasonInfo(val_type)

        start = pd.to_datetime("{y}-{md}".format(y=timestep.year, md=season_info['plant_date']))
        days_to_end = season_info['Harvest']

        end = pd.to_datetime(start) + pd.Timedelta(days=days_to_end)

        return start, end
    #End getSeasonStartEnd()

    def harvest(self, timestep, val_type='Best Guess'):

        """
        Check that it is time for harvesting the crop
        """

        assert self.plant_date != None, "Cannot harvest None crop"

        if (self.plant_date == False) or (self.plant_date == None):
            return False
        else:
            season_info = self._getPreparedSeasonInfo(val_type)
            return timestep >= (self.plant_date + pd.Timedelta(days=season_info['Harvest']))

        # season_info = self._getPreparedSeasonInfo(val_type)

        # days_from_season_start = ((pd.to_datetime(timestep) - self.plant_date) / np.timedelta64(1, 'D')).astype(int)

        # return days_from_season_start >= season_info['Harvest']

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

        gross_margin_per_Ha = (yield_per_Ha * price_per_yield) - self.variable_cost_per_Ha

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

        return self.calcTotalCropGrossMarginsPerHa(yield_per_Ha, price_per_yield)

    #End calcGrossMarginsML()

    def calcGrossMarginsPerMLHa(self, yield_per_Ha=None, price_per_yield=None):

        """
        Calculate $/ML/Ha 
        :returns: Dollar value per MegaLitre, per Hectare
        """

        if yield_per_Ha is None:
            yield_per_Ha = self.yield_per_Ha

        if price_per_yield is None:
            price_per_yield = self.price_per_yield

        return (self.calcTotalCropGrossMarginsPerHa(yield_per_Ha, price_per_yield) / self.water_use_ML_per_Ha)

    #End calcGrossMarginsMLHa()

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

    def determineCropCoefficient(self):

        """
        From Doorenbos & Pruitt 1992, Crop water requirements

        1. Determine the planting/sowing date (from local input or data regarding similar climatic zones)
        2. Determine the growing season length, and the length of crop development stages
        3. To calculate initial Kc, predict the irrigation and/or rainfall frequency. If predetermined ETo values are available, use
           Figure 6 (see Page 38) and plot initial Kc values as shown in Figure 7 (see Page 39)
        4. For the mid-season stage, select Kc value from Table 21 (see Page 40) and plot as a straight line
        5. Crop has reached full maturity (or ready for harvest within a few days).
           Select Kc value from Table 21 (Page 41) for climate conditions (need wind and relative humidity data). Here we make assumptions.
           Assume straight line from mid-season to end of growing season
        6. Can also assume straight line between end of initial stage to start of mid-season stage.
        """

#End class
