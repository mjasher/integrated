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

        self.crop_rotations = {
            'irrigated': [Crop for Crop in self.crops if 'irrigated' in Crop.name.lower()],
            'dry': [Crop for Crop in self.crops if 'dryland' in Crop.name.lower()],
        }

        self.season_started = False


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

        return crop_water_use_ML * (base_irrigation_efficiency / irrigation_efficiency) 
        # return crop_water_use_ML / irrigation_efficiency

    #End estIrrigationWaterUse()

    def getTotalFieldArea(self):
        total_area = 0
        for f in self.Farm.fields:
            total_area += f.area
        #End for

        return total_area
    #End getTotalFieldArea()

    def getNextCropInRotation(self, Field):

        """
        Rigid Crop Rotation
        Each crop is used for :math:`n` seasons within a rotation

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

        Crop = Field.Crop

        #Count number of seasons crop has been in rotation
        if (Crop is None) or (Crop.rotation_count == Crop.rotation_length):

            crop_rotation = self.crop_rotations[crop_type]

            try:
                next_crop_index = [i.name for i in crop_rotation].index(Crop.name)+1
            except AttributeError:
                next_crop_index = 0
            #End try

            try:
                #Get next crop in rotation, or first crop in rotation if not found
                next_crop = crop_rotation[next_crop_index].getCopy()
                
            except (IndexError, ValueError, AttributeError) as e:
                #Otherwise get first crop in rotation
                next_crop = crop_rotation[0].getCopy()

        else:
            Crop.rotation_count += 1
            next_crop = Crop
        #End if

        return next_crop

    #End getNextCropInRotation()

    def calcFieldCombination(self, row_id, Field, WaterSources, storage_cost_per_Ha, irrig_cost_per_Ha, max_area, logs, field_change=False, logger={}):

        """
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

        b_ub, b_eq, lp_log, water_req = logs

        # field_change = False
        implementation_change = False

        Store = Field.Storage
        Irrig = Field.Irrigation
        Crop = Field.Crop

        temp_name = "{F} {S} {I} {C}".format(F=Field.name, S=Store.name, I=Irrig.name, C=Crop.name)

        field_b_ub = [] #right hand constraints for this field
        field_b_eq = [] #right hand equality constraints for this field

        if Irrig.implemented == False:
            crop_GM = 0
        else:
            crop_GM = Crop.calcGrossMarginsPerHa()
        #End if

        est_irrigation_water_ML_per_Ha = self.estIrrigationWaterUse(Crop.water_use_ML_per_Ha, Irrig.irrigation_efficiency, self.base_irrigation_efficiency)

        flow_rate_Lps = Field.calcFlowRate()
        water_req.append(est_irrigation_water_ML_per_Ha)

        profits = {}
        #ws_max_possible_area = 0 #Max possible area with a water source
        max_possible_area = 0 #Total possible area
        for WS in WaterSources:

            water_entitlement = WS.entitlement 

            #If irrigation is not yet implemented, pumping costs is 0
            if Irrig.implemented == False:
                pumping_cost_per_Ha = 0
                water_cost_per_Ha = 0
                total_margin = 0 #- irrig_cost_per_Ha+storage_cost_per_Ha
                possible_irrigation_area = Field.area
            else:

                if 'dryland' in Irrig.name.lower():
                    pumping_cost_per_Ha = 0.0
                    water_cost_per_Ha = 0.0
                    possible_irrigation_area = Field.area
                else:

                    pumping_cost_per_Ha = WS.calcGrossPumpingCostsPerHa(flow_rate_Lps, est_irrigation_water_ML_per_Ha, head_pressure=WS.water_level, additional_head=Irrig.head_pressure)

                    water_cost_per_Ha = WS.calcWaterCostsPerHa(est_irrigation_water_ML_per_Ha)
                    # possible_irrigation_area = (water_entitlement/est_irrigation_water_ML_per_Ha)
                    possible_irrigation_area = Irrig.calcIrrigationArea(est_irrigation_water_ML_per_Ha, water_entitlement)

                    #TODO:
                    #  We can set amount of water to be sold as a constraint:
                    #    i.e. assume that farmers sell 0-100% of saved water
                    #  This must be calculated at the end, so move the below outside of this loop
                    #  Currently assumes the entire field area used
                    available_water_per_Ha = water_entitlement/Field.area
                    saved_water_value_per_Ha = (available_water_per_Ha - ((est_irrigation_water_ML_per_Ha / available_water_per_Ha) * available_water_per_Ha) ) * WS.water_value_per_ML
                #End if

                #Is it sensible to include value of unused water?
                total_margin = crop_GM #+ saved_water_value_per_Ha + additional_income
                
            #End if

            total_costs = (irrig_cost_per_Ha+pumping_cost_per_Ha+water_cost_per_Ha+storage_cost_per_Ha) #+ additional_costs #Crop costs already factored in

            if row_id not in logger:
                logger[row_id] = {}
            #End if
            
            logger['irrigation_costs'] = irrig_cost_per_Ha
            logger['pumping_costs'] = pumping_cost_per_Ha
            logger['water_costs'] = water_cost_per_Ha
            logger['storage_costs'] = storage_cost_per_Ha
            logger['total_costs'] = total_costs
            logger['total_margin'] = total_margin

            negated_profit = total_costs - total_margin

            if Irrig.implemented == True:
                ws_max_possible_area = min(Field.area, possible_irrigation_area)
            else:
                #Determine areal costs when irrigation system is not yet implemented
                ws_max_possible_area = possible_irrigation_area
            #End if

            b_ub.append(ws_max_possible_area)
            max_possible_area += min(Field.area, possible_irrigation_area)

            #This represents 'c' in LP matrix
            #Set by reference, note that this variable is not returned
            lp_log.set_value(row_id, Field.name+" "+WS.name, negated_profit)

            profits[WS.name] = negated_profit
            
        #End Water Source loop

        if max_possible_area > Field.area:
            max_possible_area = Field.area
        #End if

        #Mark as implemented after first year
        if Irrig.implemented == False:
            Irrig.implemented = True
            field_change = True

        if Store.implemented == False:
            Store.implemented = True
            field_change = True
        #End if

        b_eq.append(Field.area) if field_change else b_eq.append(None)

        #Calculate total possible irrigation area
        total_water = sum([WS.entitlement for WS in self.water_sources])
        avg_water_req = sum(water_req)/len(water_req)
        possible_irrigation_area = total_water / avg_water_req

        return field_change, max_possible_area

    #End calcFieldCombination()

    def greedyFieldCombinations(self, Field, expected_rainfall_mm, additional_costs=0, additional_income=0):
        
        """
        For a given crop, determine the optimum crop area and type, and with which water source.
        Does this in a "greedy" manner (as in Greedy Algorithm; makes myopic decisions)
        Could possibly replace this with Dynamic Programming

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
        infra_cost_per_Ha = Irrigation.calcOperationalCostPerHa()

        #Get the implemented storage
        #storage_name, Storage = self.Farm.getStorageInUse()
        Storage = Field.Storage
        storage_name = Storage.name

        #TODO: INCLUDE STORAGE COSTS
        storage_cost = Storage.calcStorageCosts(Storage.storage_capacity_ML)
        storage_maintenance_cost = Storage.calcMaintenanceCosts(Storage.storage_capacity_ML)

        #Assumes total field area is used
        storage_cost_per_Ha = (storage_cost+storage_maintenance_cost) / Field.area

        #Build linear programming equation
        optimum_field = []
        optimum = {}
        for crop_name in self.Farm.crops:

            Crop = self.Farm.crops[crop_name]

            if crop_name not in optimum:
                optimum[Crop.name] = {}
            #End if

            RAW_mm = Field.Soil.calcRAW(fraction=Crop.depletion_fraction) #Per cubic metre
            predicted_crop_yield_per_Ha = self.calcPotentialCropYield(RAW_mm, expected_rainfall_mm, Crop.et_coef, Crop.wue_coef)

            gross_margin_per_Ha = Crop.calcTotalCropGrossMarginsPerHa(predicted_crop_yield_per_Ha, Crop.price_per_yield)

            #Estimated irrigation water use
            # est_irrigation_water_ML_per_Ha = Crop.water_use_ML_per_Ha
            est_irrigation_water_ML_per_Ha = self.estIrrigationWaterUse(Crop.water_use_ML_per_Ha, Irrigation.irrigation_efficiency)

            c = []
            A_ub = []
            b_ub = []
            bounds = []
            max_irrig_area = 0
            for water_source_name in self.Farm.water_sources:

                water_source = self.Farm.water_sources[water_source_name]

                if water_source_name not in optimum[Crop.name]:
                    optimum[Crop.name][water_source_name] = {}

                flow_rate_Lps = Field.calcFlowRate() #Field.pump_operation_hours, Field.pump_operation_days, Crop=Crop
                pumping_cost_per_Ha = self.Farm.water_sources[water_source_name].calcGrossPumpingCostsPerHa(flow_rate_Lps, est_irrigation_water_ML_per_Ha, calc_func=self.Finance.calcPumpingCostsPerML)

                water_entitlement = water_source.entitlement
                possible_irrigation_area = (water_entitlement/est_irrigation_water_ML_per_Ha)
                water_value_per_ML = water_source.water_value_per_ML
                
                water_cost_per_Ha = water_source.calcWaterCostsPerHa(est_irrigation_water_ML_per_Ha)

                #Include value of saved water. 
                #Need to do this for each water source, as price of water depends on source
                available_water_per_Ha = water_entitlement/Field.area
                saved_water_value_per_Ha = (available_water_per_Ha - ((est_irrigation_water_ML_per_Ha / available_water_per_Ha) * available_water_per_Ha) ) * water_value_per_ML

                total_costs = (infra_cost_per_Ha+pumping_cost_per_Ha+water_cost_per_Ha+Crop.variable_cost_per_Ha+storage_cost_per_Ha) + additional_costs
                total_margin = (gross_margin_per_Ha + saved_water_value_per_Ha) + additional_income

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
                optimum[Crop.name][water_source].update({'area': int(round(res.x[i])),
                                                 'water_applied': res.x[i]*est_irrigation_water_ML_per_Ha, 
                                                 'total_crop_yield': (predicted_crop_yield_per_Ha*res.x[i]), 
                                                 'WUI': (predicted_crop_yield_per_Ha*res.x[i])/(res.x[i]*est_irrigation_water_ML_per_Ha),
                                                 'water_saved': water_saved(self.Farm.water_sources[water_source].entitlement, res.x[i], est_irrigation_water_ML_per_Ha),
                                                 'saved_water_value': water_saved(self.Farm.water_sources[water_source].entitlement, res.x[i], est_irrigation_water_ML_per_Ha) * self.Farm.water_sources[water_source].water_value_per_ML,
                                                 'crop_margin_per_Ha': predicted_crop_yield_per_Ha * Crop.price_per_yield if res.x[i] > 0 else 0.0
                                                 })
                total_water_use = total_water_use + optimum[Crop.name][water_source]['water_applied']
                total_area = total_area + int(round(res.x[i]))

            #End for
            optimum[Crop.name]['total_profit'] = -res.fun
            optimum[Crop.name]['total_area'] = total_area

            #Create a class that encapsulates the above configuration.
            if total_area > 0.0:
                optimum[Crop.name]['fields'] = []
                field_name = '{fn}-{cn}-{a}'.format(fn=Field.name, cn=Crop.name, a=total_area)

                #mark the crop as planted
                Crop.planted = True
                optimum[Crop.name]['fields'].append(FarmField(name=field_name, irrigation=Irrigation, crop=Crop, soil=Field.Soil, area=total_area))

            #End if

            #Add percentage water use information
            for(i, water_source) in enumerate(self.Farm.water_sources):
                optimum[Crop.name]['percent_{ws}'.format(ws=water_source)] = (optimum[Crop.name][water_source]['water_applied'] / total_water_use) if total_water_use > 0 else 0.0
            #End for

        #End for

        return optimum, res

    #End greedyFieldCombinations()

    def updateCSWD(self, Field, ETc, effective_rain, RAW):
        #Update cumulative Soil Water Deficit
        Field.c_swd = min((Field.c_swd + effective_rain) - ETc, 0)

        #Max possible soil water depletion
        if -Field.c_swd > RAW:
            Field.c_swd = -RAW
        #End if

    #End updateCSWD()

    def calcGrossIrrigationMLPerHa(self, Field, climate_params, soil_params, Crop=None, proportion=None, base_irrigation_efficiency=None):

        """
        WARNING: Currently updates Cumulative Soil Water Deficit
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

            water_to_send_mm = -Field.c_swd - nid

            debug_msg = "Need to apply water"
            
        else:
            water_to_send_mm = 0.0 #max((ETc - effective_rain), 0)

            debug_msg = "No need to apply water"
            
        #End if

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
            print "SWD is above 0 or NID, sending no water"
            print "    ", Field.c_swd
            print "    ", nid
        #End if

        # if Field.c_swd > -nid:
        #     assert water_to_send_ML_Ha == 0, "Sent water unnecessarily"

        if adj_water_to_send_ML_Ha == 0.0:
            return adj_water_to_send_ML_Ha

        #TODO:
        #Generate adjusted water source proportions to determine pumping costs

        # adjusted_water_to_send_per_Ha = 0.0
        # for WS in self.Farm.water_sources:
        #     temp_adj = (water_to_send_ML_Ha * proportion[WS.name]) #* Field.area
        #     temp_adj_ML = (temp_adj*Field.area)

        #     if (WS.entitlement - (temp_adj*Field.area)) < 0.0:
        #         adjusted_water_to_send_per_Ha += (WS.entitlement/Field.area)
        #         WS.entitlement = 0.0
        #     else:
        #         adjusted_water_to_send_per_Ha += temp_adj
        #         WS.entitlement = WS.entitlement - temp_adj_ML
        #     #End if
        # #End for

        #Get the difference from an available water source
        # total_water_to_send_ML = (water_to_send_ML_Ha*Field.area)
        # if adjusted_water_to_send_per_Ha < water_to_send_ML_Ha:
        #     for WS in self.Farm.water_sources:
        #         if WS.entitlement > 0.0:

        #             total_adj_water_ML = adjusted_water_to_send_per_Ha * Field.area

        #             if (WS.entitlement - (total_water_to_send_ML - total_adj_water_ML)) > 0.0:
        #                 adjusted_water_to_send_per_Ha += water_to_send_ML_Ha - adjusted_water_to_send_per_Ha
        #                 WS.entitlement = WS.entitlement - (total_water_to_send_ML - total_adj_water_ML)
        #             else:
        #                 adjusted_water_to_send_per_Ha += (WS.entitlement/Field.area)
        #                 WS.entitlement = 0.0
        #             #End if
        #         #End if
        #     #End for
        # #End if

        adjusted_water_to_send_per_Ha = adj_water_to_send_ML_Ha
        #actual_water_input_ML_per_Ha = adj_water_to_send_ML_Ha * Field.Irrigation.irrigation_efficiency

        # print "    Adj. irrigation (mm)", (adjusted_water_to_send_per_Ha*100)
        #Field.c_swd = min(Field.c_swd + (actual_water_input_ML_per_Ha*100), 0)
        #Field.c_swd = Field.c_swd + (adjusted_water_to_send_per_Ha*100) if Field.c_swd + (adjusted_water_to_send_per_Ha*100) < 0 else 0

        Field.c_swd = min(Field.c_swd + (adjusted_water_to_send_per_Ha*100), 0)

        return adj_water_to_send_ML_Ha

    #End calcGrossIrrigationMLPerHa()

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

            nid = Field.calcNetIrrigationDepth(timestep, base_irrigation_efficiency)
            water_to_apply[Field] = self.calcGrossIrrigationMLPerHa(Field, ETc[Field], effective_rain, nid, crop, proportion[Field], base_irrigation_efficiency)
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

        Uses French-Schultz equation, taken from Oliver et al. 2008

        TODO: Adapt modified version of `French-Schultz <http://www.regional.org.au/au/asa/2008/concurrent/assessing-yield-potential/5827_oliverym.htm/>`_

        Represents Readily Available Water - (Crop evapotranspiration * Crop Water Use Efficiency Coefficient)

        .. math::
            YP = (SSM + GSR - E) * WUE

        where

        * :math:`YP` is yield potential in kg/Ha 
        * :math:`SSM` is Stored Soil Moisture (at start of season) in mm
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

    def calcEffectiveRainfallML(self, timestep, num_events, rainfall, field_area):

        """
        Calculates effective rainfall (in ML) over the Field area
        Assumes uniform distribution of rainfall

        :param timestep: Current time step
        :param num_events: Number of rainfall events
        :param rainfall: Total rainfall that occured within time step
        :param field_area: Area
        """

        #All rainfall in winter months are considered effective
        e_rainfall = self.calcEffectiveRainfallmm(timestep, num_events, rainfall)

        return (e_rainfall / 100) * field_area
    #End calcEffectiveRainfallML()

    def calcEffectiveRainfallmm(self, timestep, num_events, rainfall):
        """
        Calculate effective rainfall in mm

        All rainfall in winter months is considered to be effective (June - August).

        Effective daily rainfall in other months is considered to be
        :math:`E_{p} = P - 5, E_{p} >= 0.0`

        Therefore, by receiving the total rainfall within a timestep, we subtract (5 * number of events)

        :math:`E_{p} = P - (5*n), E_{p} >= 0.0, n =` Number of Rainfall events

        :param timestep: Current time step
        :param num_events: Number of rainfall events
        :param rainfall: Total rainfall that occured within time step

        """
        #All rainfall in winter months are considered effective
        month = timestep.month
        e_rainfall = (rainfall - (5.0*num_events)) if month not in [6, 7, 8] else rainfall
        e_rainfall = e_rainfall if e_rainfall >= 0.0 else 0.0

        return e_rainfall
    #End calcEffectiveRainfallmm


    def setFieldComponentStatus(self, row, ignore_efficiency=False):

        """
        Sets the initial implementation status of each field component

        :param row: Pandas DataFrame Series representing a field combination
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
                # row['fields'].Crop = row['Crop'].getCopy()
            else:
                #Non-beneficial change of irrigations, remove from list
                return [np.nan, ] * len(row)
            #End if
        else:
            Field.Storage = row['Storage'].getCopy()
            Field.Irrigation = row['Irrigation'].getCopy()
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
            if (type(row[0]) is np.number) and np.isnan(row[0]):
                continue

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
            # 'Crop': Manager.crops[:]
        }

        # combination_keys = all_combinations.keys()

        return self.generateCombinations(all_combinations)

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

    def forwardTraceFieldCombinations(self, years_ahead):

        results = {}

        # for n in xrange(years_ahead)

        pass
    #End 

        
    

#End FarmManagement()