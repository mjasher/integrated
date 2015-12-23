#Manager
from __future__ import division
from integrated.Modules.Core.IntegratedModelComponent import Component
from integrated.Modules.Farm.Fields.Field import FarmField
from integrated.Modules.Farm.Fields.Soil import SoilType
from integrated.Modules.Farm.Irrigations.IrrigationPractice import IrrigationPractice

#Linear programming
from scipy.optimize import linprog as lp

#remove this when ready
from random import randint

import pandas as pd
import numpy as np

class FarmManager(Component):

    """
    Farm Manager

    .. inheritance-diagram:: integrated.Modules.Farm.Manager.FarmManager
       :parts: 2

    """

    def __init__(self, Farm):

        """
        :param Farm: Farm Object representing the Farm to manage
        """

        self.Farm = Farm

    #End __init__()

    # def determineFieldCombinations(self, expected_rainfall_mm):

    #     """
    #     Determine optimal combination of Field (and irrigation) - Crop - Water Source

    #     TODO: Include salinity costs in calculation

    #     .. math::
    #       -Crop Profit &= (Cost_{infrastructure} + Cost_{variable} + Cost_{sw pumping} - GrossMarginPerHa)*x_{1} \\\\
    #       &+ (Cost_{infrastructure} + Cost_{variable} + Cost_{gw pumping} - GrossMarginPerHa)*x_{2}

    #     where

    #     .. math::
    #       & x_{1} + x_{2} \leqslant Total Available Area \\\\
    #       & x_{1} + x_{2} \leqslant (Ent_{sw} / Irrigation_{water}) + (Ent_{gw} / Irrigation_{water}) \\\\
    #       & 0 \leqslant x_{1,2,3, ... n} \leqslant min((Ent_{sw} / Irrigation_{water}) + (Ent_{gw} / Irrigation_{water}), Total Field Area)

    #     wherein

    #     * :math:`Ent_{sw, gw}` represents Surface/groundwater entitlements 
    #     * :math:`Irrigation_{water}` = Water to send out for crop in ML/Ha, determined as :math:`Crop Water Requirement / Irrigation Efficiency`
    #     * :math:`GrossMarginPerHa` = Expected yield as provided by French-Schultz equation. See :py:meth:`calcPotentialCropYield`

    #     :param expected_rainfall_mm: Expected Growing Season Rainfall in mm
        
    #     :returns: 
    #       * field_map: List of Field, Crop, Water Source combinations considered
    #       * res: scipy.optimize.OptimizeResult object, see `linprog documentation`_

    #     .. _linprog documentation: http://docs.scipy.org/doc/scipy/reference/optimize.linprog-simplex.html

    #     """

    #     water_sources = self.Farm.water_sources
    #     crops = self.Farm.crops
    #     fields = self.Farm.fields

    #     c = []
    #     max_irrig_area = 0
    #     b_ub = []
    #     bounds = []
    #     field_map = []
    #     for Field in fields:

    #         Irrigation = Field.Irrigation
    #         infra_cost_per_Ha = (Irrigation.maintenance_rate * Irrigation.cost_per_Ha) if Irrigation.cost_per_Ha != 0.0 else Irrigation.maintenance_rate * Irrigation.replacement_cost_per_Ha
    #         infra_cost_per_Ha = infra_cost_per_Ha + Irrigation.cost_per_Ha

    #         max_irrig_area = max_irrig_area + Field.area

    #         for crop_name in crops:

    #             Crop = self.Farm.crops[crop_name]

    #             irrigation_water_ML_per_Ha = Crop.water_use_ML_per_Ha / Irrigation.irrigation_efficiency
    #             flow_rate_Lps = Field.calcFlowRate(Field.pump_operation_hours, Field.pump_operation_days, Crop=Crop)

    #             b_ub.extend([Field.area])

    #             for water_source in water_sources:

    #                 pumping_cost_per_ML = self.Farm.water_sources[water_source].calcPumpingCostsPerML(flow_rate_Lps=flow_rate_Lps)
    #                 pumping_cost_per_Ha = pumping_cost_per_ML * irrigation_water_ML_per_Ha

    #                 water_entitlement = self.Farm.water_sources[water_source].entitlement
    #                 water_value_per_ML = self.Farm.water_sources[water_source].water_value_per_ML
    #                 water_cost_per_ML = self.Farm.water_sources[water_source].cost_per_ML
    #                 water_cost_per_Ha = water_cost_per_ML * irrigation_water_ML_per_Ha

    #                 #Include value of saved water. 
    #                 #Need to do this for each water source, as price of water depends on source
    #                 #available_water_per_Ha = water_entitlement/Field.area
    #                 saved_water_value_per_Ha = 0 #(available_water_per_Ha - ((irrigation_water_ML_per_Ha / available_water_per_Ha) * available_water_per_Ha) ) * water_value_per_ML

    #                 RAW_mm = Field.Soil.calcRAW(fraction=Crop.depletion_fraction) #Per cubic metre
    #                 predicted_total_crop_yield = self.calcPotentialCropYield(RAW_mm, expected_rainfall_mm, Crop.et_coef, Crop.wue_coef)

    #                 gross_margin_per_Ha = (Crop.price_per_yield*predicted_total_crop_yield)

    #                 max_irrig_area = max_irrig_area + (water_entitlement/irrigation_water_ML_per_Ha)

    #                 c.extend([(infra_cost_per_Ha+pumping_cost_per_Ha+Crop.variable_cost_per_Ha+water_cost_per_Ha) - (gross_margin_per_Ha + saved_water_value_per_Ha)])

    #                 # print "Pred. {c} Yield (t/Ha) with {w}: {cy} | {cp}".format(c=crop_name, cy=predicted_total_crop_yield, w=water_source, cp=(infra_cost_per_Ha+pumping_cost+Crop.variable_cost_per_Ha) - (gross_margin_per_Ha + saved_water_value_per_Ha))

    #                 #Create list that maps a combination with a value in 'c'
    #                 field_map.append({'field_name': Field.name, 'crop_name': crop_name, 'water_source': water_source})

    #                 bounds.append((0, min((water_entitlement/irrigation_water_ML_per_Ha), Field.area)))
    #             #End for
    #         #End for
    #     #End for

    #     num_set = len(water_sources)

    #     #Add constraints for each water source and field combination
    #     A_ub = []
    #     for i in xrange(0, len(c), num_set):

    #         #Create a list of elements that represent fields that should be activated for each water source
    #         temp_list = [y for y in xrange(i, i+(num_set))]

    #         #Create a list of 1's and 0's. 1's represent a field-crop-watersource combination
    #         #For example, consider the following constraint
    #         #  x_{1} + x_{2} + x_{3} + x_{4} <= Total Available Area
    #         #
    #         #  Can be represented as [1, 1, 1, 1] (1x_{1}, 1x_{2}, etc.)
    #         #
    #         #  x_{1} + x_{2}, and x_{3} + x_{4} represents different fields, watered by different sources of water 
    #         #
    #         #  So to represent a single field (x_{1} + x_{2}) we have to do
    #         #  [1, 1, 0, 0] which represents 1x_{1} + 1x_{2} + 0x_{3} + 0x_{4}
    #         #  In essence, the 0's deactivate a field from consideration
    #         #
    #         #  The constraint on the above could be the Field Area
    #         #  x_{1} + x_{2} + 0x_{3} + 0x_{4} <= Area of Field 1
    #         #  0x_{1} + 0x_{2} + x_{3} + x_{4} <= Area of Field 2
    #         #
    #         A_ub.append([1 if x in temp_list else 0 for x, val in enumerate(c)])
    #     #End for

    #     #As above, but for each field as a whole
    #     num_set = int(len(c) / len(fields))
    #     for i in xrange(0, len(c), num_set):

    #         #Create a list of elements that represent fields that should be activated
    #         temp_list = [y for y in xrange(i, i+(num_set))]
    #         A_ub.append([1 if x in temp_list else 0 for x, val in enumerate(c)])
    #     #End for

    #     #Add constraints for each field as a whole
    #     for Field in fields:
    #         b_ub.extend([Field.area])
    #     #End for

    #     #Add maximum possible irrigation area as constraint
    #     b_ub.extend([max_irrig_area])

    #     #Activate all fields to constrain by maximum possible irrigation area
    #     A_ub.append([1 for x, val in enumerate(c)])

    #     res = lp(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, options={"disp": False})

    #     # water_saved = lambda ent, area, irrig_ML_per_Ha: (ent/area) - ( (irrig_ML_per_Ha / (ent/area)) * (ent/area))

    #     for i, v in enumerate(res.x):
    #         field_map[i]['area'] = v
        
    #     return field_map, res

    # #End determineFieldCombinations()

    def determineFieldCombinations(self, Field, expected_rainfall_mm):
        
        """
        For a given crop, determine the optimum crop area and type, and with which water source.
        Could possibly use this with Dynamic Programming

        .. math::
          -Crop Profit &= (Cost_{infrastructure} + Cost_{variable} + Cost_{sw pumping} - GrossMarginPerHa)*x_{1} \\\\
          &+ (Cost_{infrastructure} + Cost_{variable} + Cost_{gw pumping} - GrossMarginPerHa)*x_{2}

        where

        .. math::
          & x_{1} + x_{2} \leqslant Total Field Area \\\\
          & x_{1} + x_{2} \leqslant (Ent_{sw} / Irrigation_{water}) + (Ent_{gw} / Irrigation_{water}) \\\\
          & 0 \leqslant x_{1,2} \leqslant min((Ent_{sw} / Irrigation_{water}) + (Ent_{gw} / Irrigation_{water}), Total Field Area)

        wherein

        * :math:`Ent_{sw, gw}` represents Surface/groundwater entitlements 
        * :math:`Irrigation_{water}` = Water to send out for crop in ML/Ha, determined as :math:`Crop Water Requirement / Irrigation Efficiency`

        :param Field: Field object
        :param expected_rainfall_mm: Expected Growing Season Rainfall in mm
        :returns: Dict of area(s) irrigated by a water source and the amount of water applied, and the estimated profit

        Example return::

            "Pipe and Riser-Loam": {
                "Wheat": {
                    "percent_surface_water": 0.58497734911588484, 
                    "total_profit": 80258.945387079832, 
                    "surface_water": {
                        "costs_per_Ha": 512.7354076765841, 
                        "saved_water_value": 5391.8918918918916, 
                        "area": 10.0075, 
                        "crop_margin_per_Ha": 2774.4, 
                        "water_applied": 40.570945945945951, 
                        "water_saved": 35.945945945945944, 
                        "total_crop_yield": 57.843350000000001, 
                        "gross_margin_per_Ha": 3667.416891891892, 
                        "WUI": 1.4257333333333331,
                        "fields": [<class 'integrated.Modules.Farm.Farms.Management.FarmField'>]
                    }, 
                    "groundwater": {
                        "costs_per_Ha": 485.787871905519, 
                        "saved_water_value": 53918.918918918913, 
                        "area": 7.0999999999999996, 
                        "crop_margin_per_Ha": 2774.4, 
                        "water_applied": 28.783783783783786, 
                        "water_saved": 35.945945945945944, 
                        "total_crop_yield": 41.037999999999997, 
                        "gross_margin_per_Ha": 7343.318918918918, 
                        "WUI": 1.4257333333333331,
                        "fields": [<class 'integrated.Modules.Farm.Farms.Management.FarmField'>]
                    }, 
                    "percent_groundwater": 0.41502265088411511
                }
            }
        """

        Irrigation = Field.Irrigation
        infra_cost_per_Ha = (Irrigation.maintenance_rate * Irrigation.cost_per_Ha) if Irrigation.cost_per_Ha != 0.0 else Irrigation.maintenance_rate * Irrigation.replacement_cost_per_Ha
        infra_cost_per_Ha = infra_cost_per_Ha + Irrigation.cost_per_Ha

        optimum_field = []

        optimum = {}
        for crop_name in self.Farm.crops:

            Crop = self.Farm.crops[crop_name]

            if crop_name not in optimum:
                optimum[Crop.name] = {}
            #End if

            RAW_mm = Field.Soil.calcRAW(fraction=Crop.depletion_fraction) #Per cubic metre
            predicted_crop_yield_per_Ha = self.calcPotentialCropYield(RAW_mm, expected_rainfall_mm, Crop.et_coef, Crop.wue_coef)
            gross_margin_per_Ha = (Crop.price_per_yield*predicted_crop_yield_per_Ha)
            irrigation_water_ML_per_Ha = Crop.water_use_ML_per_Ha / Irrigation.irrigation_efficiency            

            c = []
            A_ub = []
            b_ub = []
            bounds = []
            max_irrig_area = 0
            for water_source_name in self.Farm.water_sources:

                water_source = self.Farm.water_sources[water_source_name]

                if water_source_name not in optimum[Crop.name]:
                    optimum[Crop.name][water_source_name] = {}

                flow_rate_Lps = Field.calcFlowRate(Field.pump_operation_hours, Field.pump_operation_days, Crop=Crop)
                pumping_cost_per_ML = self.Farm.water_sources[water_source_name].calcPumpingCostsPerML(flow_rate_Lps=flow_rate_Lps)
                pumping_cost_per_Ha = pumping_cost_per_ML * irrigation_water_ML_per_Ha

                water_entitlement = water_source.entitlement
                possible_irrigation_area = (water_entitlement/irrigation_water_ML_per_Ha)
                water_value_per_ML = water_source.water_value_per_ML
                water_cost_per_ML = water_source.cost_per_ML
                water_cost_per_Ha = water_cost_per_ML * irrigation_water_ML_per_Ha

                #Include value of saved water. 
                #Need to do this for each water source, as price of water depends on source
                available_water_per_Ha = water_entitlement/Field.area
                saved_water_value_per_Ha = (available_water_per_Ha - ((irrigation_water_ML_per_Ha / available_water_per_Ha) * available_water_per_Ha) ) * water_value_per_ML

                total_costs = (infra_cost_per_Ha+pumping_cost_per_Ha+water_cost_per_Ha+Crop.variable_cost_per_Ha)
                total_margin = (gross_margin_per_Ha + saved_water_value_per_Ha)

                c.extend([total_costs - total_margin])

                #Irrigation area has to be between 0 and the area constrained by water resources
                bounds.append((0, min(possible_irrigation_area, available_water_per_Ha)))

                max_irrig_area = max_irrig_area + possible_irrigation_area

                b_ub.append(possible_irrigation_area) #max possible irrigation area with this water source

                #Update information
                temp_dict = optimum[Crop.name][water_source_name]
                temp_dict['costs_per_Ha'] = total_costs
                temp_dict['gross_margin_per_Ha'] = total_margin

            #End for
            
            #Generate upper bounds (A_ub) and dependent variable constraints (b_ub)

            A_ub = []

            #Condition for each individual water resource type
            #[[1, 0, 0], [0, 1, 0], [0, 0, 1]]
            water_sources = self.Farm.water_sources
            A_ub.extend([[1 if i == j else 0 for j, v in enumerate(water_sources)] for i in xrange(0, len(water_sources))])
            
            #Condition for using a mix of water resources
            A_ub.extend([[1 for i in enumerate(c)]])

            #Irrigated area must not exceed area constrained by available water resources, or available land
            b_ub.extend([min(max_irrig_area, Field.area)])

            res = lp(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, options={"disp": False})

            #Determine water saved in ML per Ha
            water_saved = lambda ent, area, irrig_ML_per_Ha: (ent/area) - ( (irrig_ML_per_Ha / (ent/area)) * (ent/area))

            #Update information
            total_water_use = 0
            total_area = 0
            for (i, water_source) in enumerate(self.Farm.water_sources):
                optimum[Crop.name][water_source].update({'area': res.x[i], 
                                                 'water_applied': res.x[i]*irrigation_water_ML_per_Ha, 
                                                 'total_crop_yield': (predicted_crop_yield_per_Ha*res.x[i]), 
                                                 'WUI': (predicted_crop_yield_per_Ha*res.x[i])/(res.x[i]*irrigation_water_ML_per_Ha),
                                                 'water_saved': water_saved(self.Farm.water_sources[water_source].entitlement, res.x[i], irrigation_water_ML_per_Ha),
                                                 'saved_water_value': water_saved(self.Farm.water_sources[water_source].entitlement, res.x[i], irrigation_water_ML_per_Ha) * self.Farm.water_sources[water_source].water_value_per_ML,
                                                 'crop_margin_per_Ha': predicted_crop_yield_per_Ha * Crop.price_per_yield if res.x[i] > 0 else 0.0
                                                 })
                total_water_use = total_water_use + optimum[Crop.name][water_source]['water_applied']
                total_area = total_area + res.x[i]

            #End for
            optimum[Crop.name]['total_profit'] = -res.fun
            optimum[Crop.name]['total_area'] = total_area

            #Create a class that encapsulates the above configuration.
            if total_area > 0.0:
                optimum[Crop.name]['fields'] = []
                field_name = '{fn}-{cn}-{a}'.format(fn=Field.name, cn=Crop.name, a=total_area)

                optimum[Crop.name]['fields'].append(FarmField(name=field_name, irrigation=Irrigation, crop=Crop, soil=Field.Soil, area=total_area))

                
            #End if

            #Add percentage water use information
            for(i, water_source) in enumerate(self.Farm.water_sources):
                optimum[Crop.name]['percent_{ws}'.format(ws=water_source)] = (optimum[Crop.name][water_source]['water_applied'] / total_water_use) if total_water_use > 0 else 0.0
            #End for

        #End for

        return optimum, res

    #End determineFieldCombinations()

    def calcFieldIrrigationDepth(self, Field):
        return Field.calcNetIrrigationDepth(Field)
    #End calcFieldIrrigationDepth()

    def calcGrossIrrigationWaterAmount(self, Field, Crop=None):
        """
        Calculate how much water is needed to be sent out to the fields per Hectare
        Calculations are done in millimeters and then converted to ML.

        See `Estimating Vegetable Crop Water Use (Vic Ag) <http://agriculture.vic.gov.au/agriculture/horticulture/vegetables/vegetable-growing-and-management/estimating-vegetable-crop-water-use/>`_

        Especially Table 4

        TODO: Optimisation

        .. math::
            NID = D_{rz} * RAW

        where

        * :math:`NID` is Net Irrigation Depth
        * :math:`D_{rz}` is Effective Root Depth (Depth of root zone)
        * :math:`RAW` is Readily Available Water, see calcRAW() method in Soil class


        :param Field: Field object
        :returns: Total amount of water to apply in ML
        
        """

        if Crop is None:
            Crop = Field.Crop

        net_irrigation_depth = Field.calcNetIrrigationDepth(Crop.root_depth_m, Crop.depletion_fraction)

        #Check current Soil Water Deficit
        if (Field.c_swd + net_irrigation_depth) > 0.0:
            water_to_send = 0.0
        else:

            water_application = net_irrigation_depth

            while (Field.c_swd + water_application) < 0.0:
                water_application = water_application + net_irrigation_depth
            #End while

            #Add again to get it over 0.0 (?)
            #water_application = water_application + net_irrigation_depth

            water_to_send = (water_application / 100.0) * Field.area

        #End if

        return water_to_send

    #End calcGrossIrrigationWaterAmount()

    def calcWaterApplication(self):

        """
        Calculate amount of water to apply to each field

        Note: 100mm of water on 1 Hectare is equal to 1ML/Ha

        :returns: Dict of {Field Object: amount of water to apply in ML}
        """

        #Calculate amount of water to apply to each field
        water_to_apply = {}
        for Field in self.Farm.fields:
            water_to_apply[Field] = self.calcGrossIrrigationWaterAmount(Field)
        #End for

        return water_to_apply

    #End calcWaterApplication()

    def calcFieldCumulativeSWD(self, timestep, ETc, gross_water_applied):

        """
        Calculates Soil Water Deficit within a timestep and updates Field attribute

        :param timestep: Datetime (REMOVE?)
        :param ETc: Amount of evapotranspiration that occured in this timestep (irrigation efficiency)
        :param gross_water_applied: Total water applied to the field in ML
        """

        recharge = 0.0
        for field in self.Farm.fields:
            recharge = recharge + field.updateCumulativeSWD(timestep, ETc[field], gross_water_applied[field])
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

    def getHarvestableCrops(self):

        """
        TODO: Actually check if a crop is ready for harvest

        Return list of harvestable crops, and the field
        """

        fields = self.Farm.fields

        return fields
    #End

    def harvestCrops(self, fields_to_harvest):

        """
        Harvest crops
        Return harvest amount as DataFrame
        """

        crop_yields = {}
        for f in fields_to_harvest:

            crop_yields[f.crop.name] = f.harvest()

        #End for        

        return pd.DataFrame(crop_yields, index=range(1))
        
    #End harvestCrop()

    def calcPotentialCropYield(self, ssm_mm, gsr_mm, crop_evap_mm_coef, wue_mm_coef):

        """

        Uses French-Schultz equation

        TODO: Adapt modified version of `French-Schultz <http://www.regional.org.au/au/asa/2008/concurrent/assessing-yield-potential/5827_oliverym.htm/>`_

        Represents Readily Available Water - (Crop evapotranspiration * Crop Water Use Efficiency Coefficient)

        .. math::
            YP = (SSM + GSR - E) * WUE

        where

        * :math:`YP` is yield potential in kg/Ha 
        * :math:`SSM` is Stored Soil Moisture in mm
        * :math:`GSR` is Growing Season Rainfall in mm
        * :math:`E` is Crop Evaporation coefficient in mm
        * :math:`WUE` is Water Use Efficiency coefficient in kg/mm

        :param ssm_mm: Stored Soil Moisture (mm)
        :param gsr_mm: Growing Season Rainfall (mm)
        :param crop_evap_mm_coef: Crop evapotranspiration coefficient (mm)
        :param wue_mm_coef: Water Use Efficiency coefficient (kg/mm)

        :returns: Potential yield in Tonnes/Ha

        """

        #French-Schultz calculates yield in kg/Ha, so divide by 1000 to convert to tonnes per hectare.
        return ((ssm_mm + gsr_mm - crop_evap_mm_coef) * wue_mm_coef) / 1000

    #End calcPotentialCropYield()

    def calcFieldCosts(self, Field):

        """
        IN PROGRESS...
        """

        Irrigation = Field.Irrigation
        infra_cost_per_Ha = (Irrigation.maintenance_rate * Irrigation.cost_per_Ha) if Irrigation.cost_per_Ha != 0.0 else Irrigation.maintenance_rate * Irrigation.replacement_cost_per_Ha
        infra_cost_per_Ha += Irrigation.cost_per_Ha

        irrigation_water_ML_per_Ha = Crop.water_use_ML_per_Ha / Irrigation.irrigation_efficiency

        flow_rate_Lps = Field.calcFlowRate(Field.pump_operation_hours, Field.pump_operation_days, Crop=Crop)
        pumping_cost_per_ML = self.Farm.water_sources[water_source_name].calcPumpingCostsPerML(flow_rate_Lps=flow_rate_Lps)
        pumping_cost_per_Ha = pumping_cost_per_ML * irrigation_water_ML_per_Ha

        pass

        water_source = self.Farm.water_sources[water_source_name]

        water_cost_per_ML = water_source.cost_per_ML
        water_cost_per_Ha = water_cost_per_ML * irrigation_water_ML_per_Ha




        #calcFlowRate
    #End calcCosts()
    

#End FarmManagement()