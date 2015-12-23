#Management
from __future__ import division
from integrated.Modules.Core.IntegratedModelComponent import Component
from integrated.Modules.Farm.Management.Manager import FarmManager
from integrated.Modules.Farm.Fields.Field import FarmField
from integrated.Modules.Farm.Fields.Soil import SoilType
from integrated.Modules.Farm.Irrigations.IrrigationPractice import IrrigationPractice

#Linear programming
from scipy.optimize import linprog as lp

#remove this when ready
from random import randint

import pandas as pd
import numpy as np

class PlasticManager(FarmManager):

    """
    Plastic Farm Manager - Highly opportunistic management style

    .. inheritance-diagram:: integrated.Modules.Farm.Farms.Management.FarmManager
       :parts: 2

    """

    def __init__(self, Farm):

        """
        :param Farm: Farm Object representing the Farm to manage
        """

        self.Farm = Farm

    #End __init__()

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
                # optimum[Crop.name]['fields'].append(type('FarmField', (), dict(name=field_name, irrigation=Irrigation, crop=Crop, soil=Field.Soil, area=total_area)))
                optimum[Crop.name]['fields'].append(FarmField(name=field_name, irrigation=Irrigation, crop=Crop, soil=Field.Soil, area=total_area))
            #End if

            #Add percentage water use information
            for(i, water_source) in enumerate(self.Farm.water_sources):
                optimum[Crop.name]['percent_{ws}'.format(ws=water_source)] = (optimum[Crop.name][water_source]['water_applied'] / total_water_use) if total_water_use > 0 else 0.0
            #End for

        #End for

        return optimum, res

    #End determineFieldCombinations()

#End FarmManagement()