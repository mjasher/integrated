#Manager
from __future__ import division
from integrated.Modules.Core.IntegratedModelComponent import Component
from integrated.Modules.Farm.Fields.Field import FarmField
from integrated.Modules.Farm.Fields.Soil import SoilType
from integrated.Modules.Farm.Irrigations.IrrigationPractice import IrrigationPractice

#Linear programming
from scipy.optimize import linprog as lp

import pandas as pd
import numpy as np

DEBUG = False

class FarmManager(Component):

    """
    Farm Manager

    """

    def __init__(self, Farm, water_sources, storages, irrigations, crops, LpInterface, Finance, livestocks=None):

        """
        :param Farm: Farm Object representing the Farm to manage
        :param water_sources: List of water_sources to choose from
        :param irrigations: List of irrigation systems to choose from
        :param crops: List of crops to choose from
        :param LpInterface: Interface to use for Linear Programming
        :param Finance: object housing financial calculations to use
        :param livestocks: List of livestock to choose from
        """

        self.Farm = Farm
        self.water_sources = water_sources
        self.storages = storages
        self.irrigations = irrigations
        self.crops = crops
        self.LpInterface = LpInterface
        self.Finance = Finance
        self.livestocks = livestocks

        self.farm_area = self.getTotalFieldArea()

        if crops != None:
            self.crop_rotations = {
                'irrigated': [Crop for Crop in self.crops if 'irrigated' in Crop.name.lower()],
                'dry': [Crop for Crop in self.crops if 'dryland' in Crop.name.lower()],
            }

        self.season_started = False

        self.crop_rotation_counter = {}


    #End __init__()

    def estIrrigationWaterUse(self, crop_water_use_ML, irrigation_efficiency, base_irrigation_efficiency=0.7):

        """
        Simple estimate of irrigation water to apply.
        Used to determine irrigation investment.

        It seems figures given in the literature already include water losses and precipitation.
        e.g. if a crop is said to need 6ML/Ha/Season, it is with flood irrigation + "usual" rainfall

        Crop water needs are calculated from the base irrigation efficiency.
        In this case, it is whatever flood irrigation efficiency is.

        Example::

            A winter crop needs 6ML/Ha with flood irrigation.
            Flood irrigation is said to be ~0.7 efficient

            Base crop use &= 6 * 0.7
                          &= 4.2 ML/Ha

            Farmer then upgrades irrigation to spray, which is 0.8 efficient

            Base crop use / 0.8 &= 4.2 / 0.8
                                &= 5.25

        :param crop_water_use_ML: How much water the crop is said to require
        :param irrigation_efficiency: A percentage indicating how much water actually gets to the field

        """

        return (crop_water_use_ML * base_irrigation_efficiency) / irrigation_efficiency
        # return crop_water_use_ML / irrigation_efficiency

    #End estIrrigationWaterUse()

    def getTotalFieldArea(self):

        total_area = 0

        if (self.Farm != None) and (self.Farm.fields != None):
            for f in self.Farm.fields:
                total_area += f.area
            #End for
        #End if

        return total_area
    #End getTotalFieldArea()

    def getAvailableCropChoices(self):
        crop_choices = {}
        for Field in self.Farm.fields:
            crop_choices[Field.name] = [self.getNextCropInRotation(Field).name]
        #End for
        
        return crop_choices
    #End getAvailableCropChoices()

    def getNextCropInRotation(self, Field, increment=True):

        """
        Rigid Crop Rotation
        Each crop is used for :math:`n` seasons within a rotation

        :param Field: FarmField object
        :param increment: (bool) increment crop rotation counter, defaults to True

        Return the current or next crop within the specified rotation
        
        """

        irrig_name = Field.Irrigation.name.lower()

        if 'dryland' in irrig_name:
            crop_type = 'dry'
        elif 'irrigated' in irrig_name:
            crop_type = 'irrigated'
        else:
            #Default if not found
            crop_type = 'irrigated'
        #End if

        assert len(self.crop_rotations[crop_type]) > 0, 'No {} crop specified!'.format(crop_type)

        crop_rotation = self.crop_rotations[crop_type]

        Crop = Field.Crop

        if Crop == None:
            next_crop = crop_rotation[0].getCopy()
            self.crop_rotation_counter[next_crop.name] = self.crop_rotation_counter.get(next_crop.name, 0)

            return next_crop
        else:
            self.crop_rotation_counter[Crop.name] = self.crop_rotation_counter.get(Crop.name, 0)

            if self.crop_rotation_counter[Crop.name] < Crop.rotation_length:
                self.crop_rotation_counter[Crop.name] += 1
                next_crop = Crop.getCopy()
            else:
                next_crop_index = [crop.name for crop in crop_rotation].index(Crop.name)+1
                self.crop_rotation_counter[Crop.name] = 0

                next_crop = crop_rotation[next_crop_index].getCopy() if next_crop_index < len(crop_rotation) \
                                                                     else crop_rotation[0].getCopy()
            #End if
            
        #End if

        return next_crop

    #End getNextCropInRotation()

    def calcFieldCombination(self, row_id, Field, WaterSources, storage_cost_per_Ha, irrig_cost_per_Ha, logs, field_change=False, logger={}, water_applied=None):

        """

        Generate the c and b_ub values for the given field

        If the Objective Function follows the form of 
        
        :math:`P_{n}*x_{n}`

        where 
        * P_{n} is the Negated Net Profit (Cost - Gross Margin) of a given option
        * x_{n} is the Area constrained by Water Resources and Available Land

        and the aim is to minimize the negated profits (i.e. maximise profits).

        P_{n} then represents the Net Profit for a given combination of 
        * Field
        * Storage
        * Irrigation
        * Crop (or livestock?)

        As an example, consider a farm with two fields, a single storage, two irrigation choices, two crops, and the ability to pump water from a surface water 
        source or a groundwater source.

        In total, there would be 16 possible combinations (eight possible field configurations watered from two sources of water)

        ========= ========= ============ ======== ==============
        Field      Storage   Irrigation   Crop     Water Source
        ========= ========= ============ ======== ==============
        Field A    Farm Dam   Flood       Wheat    Surface Water
        Field A    Farm Dam   Flood       Wheat    Groundwater
        Field A    Farm Dam   Flood       Canola   Surface Water
        Field A    Farm Dam   Flood       Canola   Groundwater
        Field A    Farm Dam   Spray       Wheat    Surface Water
        Field A    Farm Dam   Spray       Wheat    Groundwater
        Field A    Farm Dam   Spray       Canola   Surface Water
        Field A    Farm Dam   Spray       Canola   Groundwater
        Field B    Farm Dam   Flood       Wheat    Surface Water
        Field B    Farm Dam   Flood       Wheat    Groundwater
        Field B    Farm Dam   Flood       Canola   Surface Water
        Field B    Farm Dam   Flood       Canola   Groundwater
        Field B    Farm Dam   Spray       Wheat    Surface Water
        Field B    Farm Dam   Spray       Wheat    Groundwater
        Field B    Farm Dam   Spray       Canola   Surface Water
        Field B    Farm Dam   Spray       Canola   Groundwater
        ========= ========= ============ ======== ==============

        Linear Programming is used to determine the proportion of surface or groundwater use.
        This is done for a given combination of field-crop configurations.

        Hence the objective function for the farm fields, irrigation system, crop and soil type is:

        .. math::
            \min\sum_{n=1}^{m}(G_{n}X_{n} + G_{n}Y_{n})

        s.t:

        .. math::

            X_{n} \leqslant \min(A_{n}, A_{sw}), A_{sw} = \\frac{X_{e}}{c_{nw}}

            Y_{n} \leqslant \min(A_{n}, A_{gw}), A_{gw} = \\frac{Y_{e}}{c_{nw}}

            X_{n} + Y_{n} \leqslant A_{n}

            \sum_{n=1}^{m}(X_{n} + Y_{n}) \leqslant \min(A_{T}, A_{p})

        Where :math:`n` represents a given field with an irrigation system and crop choice and :math:`m` is the
        number of fields associated with a farm; :math:`G` is the negated net profit per Hectare; and :math:`X_{n}` and :math:`Y_{n}`
        represent the area to be watered by surface and groundwater respectively. Surface and groundwater entitlements 
        (:math:`X_{e}` and :math:`Y_{e}`) and crop water requirements per hectare (:math:`c_{nw}`) is used to calculate
        the maximum possible irrigation area.

        :math:`A_{T} = \sum_{n=1}^{m}(A_{n})`

        :math:`A_{p} = \\frac{W_{ent}}{\sum_{n=1}^{m}(c_{nw})/m}` is the maximum possible irrigation area

        In Python Scipy LinProg, this is represented as:: 

            c = [Profit_A_sw, Profit_A_gw, Profit_B_sw, Profit_B_gw]
            A_ub = [[1, 1, 0, 0], [0, 0, 1, 1]]
            b_ub = [Area of Field A, Area of Field B]
            bounds = (0, Total Field Area)

        In cases where irrigation system is being implemented, the farmer cannot grow crops to make money, but still incurs costs (implementation, water storage, etc).
        To reflect this an equality constraint is used:

        :math:`G_{n} = Total Costs`

        :math:`X_{n}` and :math:`Y_{n} = A_{n}`
        """

        b_ub, b_eq, c_log, water_req, max_area = logs

        # field_change = False
        implementation_change = False

        Store = Field.Storage
        Irrig = Field.Irrigation
        Crop = Field.Crop

        temp_name = "{F} {S} {I}".format(F=Field.name, S=Store.name, I=Irrig.name)

        field_b_ub = [] #right hand constraints for this field
        field_b_eq = [] #right hand equality constraints for this field

        if Irrig.implemented == False:
            crop_profit = 0
        else:
            crop_profit = Crop.calcGrossMarginsPerHa()
        #End if

        if water_applied == None:
            w_app = 0

        #An attempt to account for the water already applied. Not necessary if calculations are done on total growing season allocation
        #w_app = 0 if water_applied == None else water_applied[Field]
        est_irrigation_water_ML_per_Ha = self.estIrrigationWaterUse(Crop.water_use_ML_per_Ha, Irrig.irrigation_efficiency, self.base_irrigation_efficiency)

        flow_rate_Lps = Field.calcFlowRate()
        water_req.append(est_irrigation_water_ML_per_Ha)

        profits = {}
        #ws_max_possible_area = 0 #Max possible area with a water source
        max_possible_area = 0 #Total possible area
        additional_costs = 0
        for WS in WaterSources:

            water_allocation = WS.allocation

            #If irrigation is not yet implemented, pumping costs is 0
            if (Irrig.implemented == False) or (WS.implemented == False):
                pumping_cost_per_Ha = 0
                water_cost_per_Ha = 0 #WS.calcTotalCostsPerHa() not considering implementation cost of water source (e.g. bore construction)
                total_margin = 0 #- irrig_cost_per_Ha+storage_cost_per_Ha
                possible_irrigation_area = Field.area
            else:

                if 'dryland' in Irrig.name.lower():
                    pumping_cost_per_Ha = 0.0
                    water_cost_per_Ha = 0.0
                    possible_irrigation_area = Field.area
                else:

                    pumping_cost_per_Ha = WS.calcGrossPumpingCostsPerHa(flow_rate_Lps, est_irrigation_water_ML_per_Ha, head_pressure=Irrig.head_pressure, additional_head=WS.water_level)

                    possible_irrigation_area = Irrig.calcIrrigationArea(est_irrigation_water_ML_per_Ha, water_allocation)

                    #Includes pump maintenance cost
                    water_cost_per_Ha = WS.calcTotalCostsPerHa(est_irrigation_water_ML_per_Ha, possible_irrigation_area)

                    #calculate overuse cost
                    #TODO: FIX THIS QUICK AND DIRTY CALCULATION, OVERUSE COST ($2000/ML) SHOULD COME FROM EXTERNAL DATA
                    if (water_allocation - (est_irrigation_water_ML_per_Ha * possible_irrigation_area) ) < 0:
                        additional_costs += abs(water_allocation - (est_irrigation_water_ML_per_Ha * possible_irrigation_area)) * 2000

                    #TODO:
                    #  We can set amount of water to be sold as a constraint:
                    #    i.e. assume that farmers sell 0-100% of saved water
                    #  This must be calculated at the end, so move the below outside of this loop
                    #  Currently assumes the entire field area used
                    available_water_per_Ha = water_allocation/Field.area
                    saved_water_value_per_Ha = (available_water_per_Ha - ((est_irrigation_water_ML_per_Ha / available_water_per_Ha) * available_water_per_Ha) ) * WS.trade_value_per_ML
                #End if

                #Is it sensible to include value of unused water?
                total_margin = crop_profit #+ saved_water_value_per_Ha + additional_income
                
            #End if

            #Activate water source
            if WS.implemented == False:
                WS.implemented = True
            #End if

            #Crop costs already factored in above (total_margin)
            total_costs = (irrig_cost_per_Ha+pumping_cost_per_Ha+water_cost_per_Ha+storage_cost_per_Ha) + additional_costs

            # print "pump maintenance cost:", pump_maintenance_cost
            # print "Total Costs per Ha:", total_costs
            # print "---------------------------"

            # if row_id not in logger:
            #     logger[row_id] = {}
            # #End if
            
            # logger['irrigation_costs'] = irrig_cost_per_Ha
            # logger['pumping_costs'] = pumping_cost_per_Ha
            # logger['water_costs'] = water_cost_per_Ha
            # logger['storage_costs'] = storage_cost_per_Ha
            # logger['total_costs'] = total_costs
            # logger['total_margin'] = total_margin
            
            negated_profit = total_costs - total_margin

            if Irrig.implemented == True:
                ws_max_possible_area = min(Field.area, possible_irrigation_area)

                ws_max_possible_area = 0 if ws_max_possible_area < 0 else ws_max_possible_area

                #assert ws_max_possible_area >= 0, 'Area cannot be below 0, {} \n Water Alloc: {} \n Water Use: {}'.format(ws_max_possible_area, water_allocation, est_irrigation_water_ML_per_Ha)
            else:
                #Determine areal costs when irrigation system is not yet implemented
                ws_max_possible_area = Field.area
            #End if

            max_possible_area += ws_max_possible_area #min(Field.area, ws_max_possible_area)

            #This represents 'c' in LP matrix
            #Set by reference, note that this variable is not returned
            #c_log.set_value(row_id, Field.name+" "+WS.name, negated_profit)
            c_log.set_value(row_id, temp_name+" "+WS.name, negated_profit)
            b_ub.set_value(0, temp_name+" "+WS.name, ws_max_possible_area)
            #b_ub_log.set_value(row_id, temp_name+" "+WS.name, ws_max_possible_area)

            profits[WS.name] = negated_profit
            
        #End Water Source loop

        # import sys; sys.exit()

        max_possible_area = min(max_possible_area, Field.area)

        #Mark as implemented after first year
        if Irrig.implemented == False:
            Irrig.implemented = True
            field_change = True
        #End if

        if Store.implemented == False:
            Store.implemented = True
            field_change = True
        #End if

        #If field has changed (i.e. irrigation system was upgraded) then apply cost for entire area
        b_eq.append(Field.area) if field_change else b_eq.append(None)

        max_area.append(max_possible_area)

        return field_change

    #End calcFieldCombination()

    def updateCSWD(self, Field, ETc, effective_rain, RAW):

        """
        Updates Cumulative Soil Water Deficit.
        WARNING: Not the same as the function in the Field module, which should be used with caution.
        """

        #Update cumulative Soil Water Deficit
        Field.c_swd = min((Field.c_swd + effective_rain) - ETc, 0)

        #Max possible soil water depletion
        if -Field.c_swd > RAW:
            Field.c_swd = -RAW
        #End if

    #End updateCSWD()

    def calcIrrigationMLPerHa(self, Field, climate_params, soil_params, Crop=None, proportion=None, base_irrigation_efficiency=None):

        """
        WARNING: Currently updates Cumulative Soil Water Deficit (i.e. this is a method with side effect)
        """

        if 'dryland' in Field.Irrigation.name.lower():
            return 0.0

        if base_irrigation_efficiency == None:
            base_irrigation_efficiency = self.base_irrigation_efficiency

        if Crop == None:
            Crop = Field.Crop
        #End if

        ETc = climate_params["ETc"]
        effective_rain = climate_params["e_rainfall"]
        nid = soil_params["nid"]
        RAW = soil_params["RAW"]

        #Update cumulative Soil Water Deficit
        self.updateCSWD(Field, ETc, effective_rain, RAW)

        #Check current Soil Water Deficit
        adj_water_to_send_ML_Ha = 0.0

        #Apply Crop Water Use once NID is reached
        #Only apply enough water for it to maintain water level at NID
        if -Field.c_swd >= nid:

            water_to_send_mm = -Field.c_swd * 0.5 #-Field.c_swd / 4  #-Field.c_swd - nid

            debug_msg = "Need to apply water"
            
        else:
            water_to_send_mm = 0.0 #max((ETc - effective_rain), 0)

            debug_msg = "No need to apply water"
            
        #End if

        if DEBUG:
            print debug_msg
            print "    c_swd: ", Field.c_swd
            print "    wd: ", (ETc - effective_rain)
            print "    nid: ", -nid
            #print "    WTS: ", water_to_send_mm
            print "    Sending (mm/Ha)", water_to_send_mm


        water_to_send_ML_Ha = water_to_send_mm / 100
        adj_water_to_send_ML_Ha = (water_to_send_mm / Field.Irrigation.irrigation_efficiency) / 100

        assert adj_water_to_send_ML_Ha >= 0, "Cannot send negative amounts of water!"

        if (Field.c_swd > 0.0): #(0.0-nid): #or (Field.c_swd > -nid)

            if DEBUG:
                print "SWD is above 0 or NID, sending no water"
                print "    ", Field.c_swd
                print "    ", nid
            #End if
        #End if

        # if Field.c_swd > -nid:
        #     assert water_to_send_ML_Ha == 0, "Sent water unnecessarily"

        if adj_water_to_send_ML_Ha == 0.0:
            return adj_water_to_send_ML_Ha

        #TODO:
        #Generate adjusted water source proportions to determine pumping costs
        #Update water allocation amount after irrigation use
        #Currently the area to be irrigated remains static over the course of a season
        #this doesn't affect pumping cost, but later when we incorporate in-season allocation adjustment
        #it will become an issue

        #for WS in self.Farm.water_sources:

        #adjusted_water_to_send_per_Ha = adj_water_to_send_ML_Ha
        #actual_water_input_ML_per_Ha = adj_water_to_send_ML_Ha * Field.Irrigation.irrigation_efficiency

        # print "    Adj. irrigation (mm)", (adjusted_water_to_send_per_Ha*100)
        #Field.c_swd = min(Field.c_swd + (actual_water_input_ML_per_Ha*100), 0)
        #Field.c_swd = Field.c_swd + (adjusted_water_to_send_per_Ha*100) if Field.c_swd + (adjusted_water_to_send_per_Ha*100) < 0 else 0

        #Field.c_swd = min(Field.c_swd + (adjusted_water_to_send_per_Ha*100), 0)
        Field.c_swd = min(Field.c_swd + water_to_send_mm, 0)

        return adj_water_to_send_ML_Ha

    #End calcIrrigationMLPerHa()

    def updateWaterAllocations(self, water_to_apply_ML, proportion):
        """
        Subtract the amount of water to apply to a field from the available water allocations

        If water allocations resolve to a negative amount over the course of a season, it means excess orders/extractions occurred

        #TODO Incorporate overuse costs

        :param water_to_apply_ML: Amount of water to apply to a field
        :param proportion: Dict representing the proportion of water from each water source to use, e.g. {'Surface': 1.0, 'Groundwater': 0.0}

        :returns: void, updates allocation volume
        """

        for WS in self.Farm.water_sources:
            ws_proportion = water_to_apply_ML * proportion[WS.name]
            WS.allocation = WS.allocation - ws_proportion
        #End for

    #End updateWaterAllocations()


    def calcWaterApplication(self, ETc, effective_rain, timestep, proportion, base_irrigation_efficiency=None, crop=None):

        """
        Calculate amount of water to apply to each field

        Note: 100mm of water on 1 Hectare is equal to 1ML/Ha

        :param ETc: Dict of ETc for each field
        :param effective_rain: Effective rain for area (we are assuming uniform distribution)
        :param proportion: Dict of proportion of water to be taken from each water source, for each field
        :param base_irrigation_efficiency: Irrigation efficiency to compare against; defaults to None, which uses the value set for Manager
        :param crop: Dict of crops grown in each field. Defaults to none.

        :returns: Dict of {Field Object: amount of water to apply in ML}
        """

        #Calculate amount of water to apply to each field
        water_to_apply = {}

        if base_irrigation_efficiency == None:
            base_irrigation_efficiency = self.base_irrigation_efficiency

        for Field in self.Farm.fields:
            nid = Field.calcNetIrrigationDepth(timestep)
            water_to_apply[Field] = self.calcIrrigationMLPerHa(Field, ETc[Field], effective_rain, nid, crop, proportion[Field], base_irrigation_efficiency)
        #End for

        return water_to_apply

    #End calcWaterApplication()

    def calcFieldCumulativeSWD(self, timestep, ETc, gross_water_applied):

        """
        Calculates Soil Water Deficit within a timestep and updates Field attribute

        :param timestep: Datetime (REMOVE?)
        :param ETc: Amount of evapotranspiration that occured in this timestep (irrigation efficiency)
        :param gross_water_applied: Dict of total water applied to each field in ML
        """

        recharge = 0.0
        for field in self.Farm.fields:
            recharge = recharge + field.updateCumulativeSWD(gross_water_applied[field], ETc[field])
        #End field

        return recharge

    #End calcCumulativeSWD()

    def applyWater(self, water_to_apply):

        """
        Applies water to each field under management

        :returns: total recharge
        """

        #water_to_apply = self.calcWaterApplication(Fields)
        #Recharge = (Rainfall + Applied Water) - (ETc + SWD_i)

        recharge = 0.0
        for field in self.Farm.fields:
            recharge = recharge + field.applyWater(water_to_apply[field])

        #End for

        return recharge
    #End applyWater()

    def calcPotentialCropYield(self, ssm_mm, gsr_mm, crop_evap_mm_coef, wue_mm_coef, plant_RAW, scaling_factor=0.6):

        """

        Uses French-Schultz equation, taken from `Oliver et al. 2008 (Equation 1) <http://www.regional.org.au/au/asa/2008/concurrent/assessing-yield-potential/5827_oliverym.htm/>`_
        
        Could use the farmer friendly modified version as given in the above.

        Represents Readily Available Water - (Crop evapotranspiration * Crop Water Use Efficiency Coefficient)

        .. math::
            YP = (SSM + GSR - E) * WUE

        where :math:`GSR` represents the sum of the monthly 

        where

        * :math:`YP` is yield potential in kg/Ha 
        * :math:`SSM` is Stored Soil Moisture (at start of season) in mm
        * :math:`GSR` is Growing Season Rainfall in mm
        * :math:`E` is Crop Evaporation coefficient in mm, the amount of rainfall required before the crop will start to grow, commonly 110mm
        * :math:`WUE` is Water Use Efficiency coefficient in kg/mm

        :param ssm_mm: Stored Soil Moisture (mm)
        :param gsr_mm: Growing Season Rainfall (mm)
        :param crop_evap_mm_coef: Crop evapotranspiration coefficient (mm)
        :param wue_mm_coef: Water Use Efficiency coefficient (kg/mm)
        :param plant_RAW: Maximum Readily Available Water for the plant in the soil. SSM cannot exceed this value
        :param scaling_factor: Amount of water applied no longer increases potential yield above a certain threshold determined by SSM, defaulting to 400mm

        :returns: Potential yield in tonnes/Ha

        """

        ssm_mm = min(plant_RAW, ssm_mm)

        #Oliver et al. 2009, water above a threshold does not contribute to crop yield
        #This is for Western Australia, but may be applicable...
        #TODO: Clean this up, quick and dirty implementation, I'm sorry future maintainer :(
        if (ssm_mm >= 40) and (ssm_mm < 50):
            threshold = 225
        elif (ssm_mm >= 50) and (ssm_mm < 60):
            threshold = 235
        elif (ssm_mm >= 60) and (ssm_mm < 70):
            threshold = 245
        elif (ssm_mm >= 70) and (ssm_mm < 80):
            threshold = 260
        elif (ssm_mm >= 80) and (ssm_mm < 90):
            threshold = 270
        elif (ssm_mm >= 90) and (ssm_mm < 100):
            threshold = 280
        elif (ssm_mm >= 100) and (ssm_mm < 110):
            threshold = 290
        elif (ssm_mm >= 110) and (ssm_mm < 120):
            threshold = 300
        elif (ssm_mm >= 120) and (ssm_mm < 130):
            threshold = 315
        elif (ssm_mm >= 130) and (ssm_mm < 140):
            threshold = 325
        elif (ssm_mm >= 140) and (ssm_mm < 150):
            threshold = 335
        elif (ssm_mm >= 150) and (ssm_mm < 160):
            threshold = 345
        elif (ssm_mm >= 160) and (ssm_mm < 170):
            threshold = 355
        elif (ssm_mm >= 170) and (ssm_mm < 180):
            threshold = 365
        elif (ssm_mm >= 190) and (ssm_mm < 200):
            threshold = 375
        elif (ssm_mm >= 190) and (ssm_mm < 200):
            threshold = 385
        elif (ssm_mm >= 200):
            threshold = 395
        #End if

        if 'threshold' in locals():
            if gsr_mm > threshold:
                gsr_mm = max(gsr_mm * scaling_factor, threshold)
            #End if
        else:
            if gsr_mm > 400:
                gsr_mm = max(gsr_mm * scaling_factor, 400)

        #gsr_mm = 400

        return max(((ssm_mm + gsr_mm - crop_evap_mm_coef) * wue_mm_coef) / 1000, 0)

    #End calcPotentialCropYield()

    def calcEffectiveRainfallML(self, timestep, rainfall_data, field_area, winter_months=[6,7,8]):

        """
        Calculate effective rainfall in ML

        :param timestep: Datetime object of current timestep
        :param rainfall_data: Pandas series containing rainfall data
        :param field_area: numeric value representing field area of farm
        :param winter_months: List of numeric values representing winter months, where 1 = Jan, 2 = Feb, ... 12 = Dec

        :returns: Sum of effective rainfall in ML

        """

        #All rainfall in winter months are considered effective
        e_rainfall = self.calcEffectiveRainfallmm(timestep, rainfall_data, winter_months)

        return (e_rainfall / 100) * field_area
    #End calcEffectiveRainfallML()

    def calcEffectiveRainfallmm(self, timestep, rainfall_data, winter_months):
        """
        Calculate effective rainfall in mm

        All rainfall in winter months is considered to be effective (June - August).

        Effective daily rainfall in other months is considered to be
        :math:`E_{p} = max{P - 5, 0}`

        Therefore, for each rainfall event within the given timestep we apply the above:

        :math:`E_{p} = { \sum_{t=1}^{m}(P) if month is June to August, or \sum_{t=1}^{m}(max{P - 5, 0}) if other months`

        :param timestep: Current time step
        :param rainfall_data: Rainfall data for timestep
        :param winter_months: List of month numbers to consider as winter

        """

        month = timestep.month

        #Calculate effective rainfall
        if month not in winter_months:
            rainfall_data = rainfall_data - 5
            rainfall_data.loc[rainfall_data < 0] = 0
        #End if

        return rainfall_data.sum()

    #End calcEffectiveRainfallmm()

    def setFieldComponentStatus(self, row, ignore_efficiency=False):

        """
        Sets the initial implementation status of each field component

        :param row: Pandas DataFrame Series representing a field combination
        :param ignore_efficiency: (bool) True = Skip comparison of current and proposed irrigations, False = Compare efficiency
        """

        #Because all_combinations are passed by reference, have to reassign a copy
        row['fields'] = row['fields'].getCopy()

        Field = row['fields']

        if Field.Storage.name == row['Storage'].name:
            row['Storage'].implemented = True
        else:
            row['Irrigation'].implemented = False

        if Field.Irrigation.name == row['Irrigation'].name:
            row['Irrigation'].implemented = True
        else:
            row['Irrigation'].implemented = False

        if ignore_efficiency == False:
            if (row['Irrigation'].irrigation_efficiency >= Field.Irrigation.irrigation_efficiency) or ('dryland' in Field.Irrigation.name.lower()):
                # row['fields'].WaterSource = row['WaterSource'].getCopy()
                Field.Storage = row['Storage'].getCopy()
                Field.Irrigation = row['Irrigation'].getCopy()
                Field.Crop = row['Crop'].getCopy()

            else:
                #Non-beneficial change of irrigations, remove from list
                return [np.nan, ] * len(row)
            #End if
        else:
            Field.Storage = row['Storage'].getCopy()
            Field.Irrigation = row['Irrigation'].getCopy()

            if (Field.Crop == None) or Field.Crop.name == row['Crop'].name:
                Field.Crop = row['Crop'].getCopy()
            #End if

        #End if

        return row
    #End updateFieldComponents()

    def setupFieldComponentsStatus(self, combinations):

        """
        Set implementation status and remove unneeded combinations for each row in given DataFrame. 
        Each row represents a field combination
        """

        field_combi = {}

        #Ignore irrigation efficiency check if only one combination available
        if len(combinations) == 1:
            ignore_efficiency = True
        else:
            ignore_efficiency = False
        #End if
        
        for i, row in combinations.iterrows():

            row = self.setFieldComponentStatus(row, ignore_efficiency)

            #If field element is NaN
            #Raises exception when variable is class, safe to pass
            try:
                #If all items in row is NaN
                if all(np.isnan(x) for x in row):
                    continue
            except TypeError:
                pass

            field_name = row['fields'].name
            if field_name not in field_combi:
                field_combi[field_name] = []

            field_combi[field_name].append(row['fields'].getCopy())
        #End for

        assert len(field_combi) > 0, "List of field combinations cannot be empty"

        return field_combi

    #End

    def generateFieldCombinations(self):

        """
        Generate all possible combinations of fields, storages and irrigations
        """

        all_combinations = {
            'fields': [field.getCopy() for field in self.Farm.fields],
            # 'WaterSource': Manager.water_sources[:],
            'Storage': [store.getCopy() for store in self.storages], #self.storages[:],
            'Irrigation': [irrig.getCopy() for irrig in self.irrigations],
            'Crop': [crop.getCopy() for crop in self.crops]
        }

        #Generate all combinations
        all_combinations = self.generateCombinations(all_combinations)

        #Create field objects based on generated field setup combinations
        field_combi = self.setupFieldComponentsStatus(all_combinations)

        #Create all possible combinations of fields
        field_combinations = self.generateCombinations(field_combi)

        #Filter field_combinations down to available crop choices
        crop_choices = self.getAvailableCropChoices()

        field_combinations = field_combinations.apply(lambda x: x.map(lambda y: y if y.Crop.name in crop_choices[y.name] else np.nan))
        field_combinations = field_combinations.dropna().reset_index(drop=True)
        
        return field_combinations

    #End generateFieldCombinations()

    def generateCombinations(self, combs):

        """
        Generates all possible combinations of farm components
        """

        import itertools
        #Generate all combinations of available farm components
        all_combinations = [dict(itertools.izip_longest(combs, v)) for v in itertools.product(*combs.values())]
        all_combinations = pd.DataFrame(all_combinations)

        #Replace with a copy; these objects should be compartmentalised
        for col in all_combinations:
            for i, Field in all_combinations[col].iteritems():
                all_combinations.loc[i, col] = Field.getCopy()
            #End for
        #End for

        return all_combinations
    #End generateCombinations()

    def calcStorageCostsPerHa(self, Field):
        Store = Field.Storage
        storage_cost = Store.calcStorageCosts(Store.storage_capacity_ML)
        storage_maintenance_cost = Store.calcMaintenanceCosts(Store.storage_capacity_ML)

        if self.getTotalFieldArea() == 0:
            storage_cost_per_Ha = (storage_cost + storage_maintenance_cost) * Store.storage_capacity_ML
        else:
            #WARNING: Storage Cost per Ha is calculated using Field Area, not actual used area
            storage_cost_per_Ha = (storage_cost+storage_maintenance_cost) / self.getTotalFieldArea()
        #End if

        assert np.isinf(storage_cost_per_Ha) == False, "Storage cost cannot be infinite"

        return storage_cost_per_Ha

    #End calcStorageCostsPerHa()

        
    

#End FarmManagement()