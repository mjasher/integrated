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

    def __init__(self, Farm, water_sources, storages, irrigations, crops, LpInterface, livestocks=None):

        """
        :param Farm: Farm Object representing the Farm to manage
        :param water_sources: List of water_sources to choose from
        :param irrigations: List of irrigation systems to choose from
        :param crops: List of crops to choose from
        :param LpInterface: Interface to use for Linear Programming
        :param livestocks: List of livestock to choose from
        """

        self.Farm = Farm
        self.water_sources = water_sources
        self.storages = storages
        self.irrigations = irrigations
        self.crops = crops
        self.LpInterface = LpInterface
        self.livestocks = livestocks


    #End __init__()

    def estIrrigationWaterUse(self, crop_water_use_ML, irrigation_efficiency, base_irrigation_efficiency=0.7):

        """
        Estimate amount of irrigation water to send out.

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

    def calcFieldCombination(self, row_id, Field, WaterSources, storage_cost_per_Ha, irrig_cost_per_Ha, max_area, logs):

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

        b_ub, b_eq, lp_log, b_ub_log, b_eq_log, water_req = logs

        field_change = False
        implementation_change = False

        Store = Field.Storage
        Irrig = Field.Irrigation
        Crop = Field.Crop

        temp_name = "{F} {S} {I} {C}".format(F=Field.name, S=Store.name, I=Irrig.name, C=Crop.name)

        field_b_ub = []
        field_b_eq = []

        if Irrig.implemented == False:
            crop_GM = 0
        else:
            crop_GM = Crop.calcGrossMarginsPerHa()
        #End if

        est_irrigation_water_ML_per_Ha = self.estIrrigationWaterUse(Crop.water_use_ML_per_Ha, Irrig.irrigation_efficiency, self.base_irrigation_efficiency)
        flow_rate_Lps = Field.calcFlowRate()

        water_req.append(est_irrigation_water_ML_per_Ha)

        profits = {}
        this_max_area = 0 #Max possible area with a water source
        max_possible_area = 0 #Total possible area
        for WS in WaterSources:

            #Amount of usable water dependent on irrigation efficiency
            water_entitlement = WS.entitlement #* Irrig.irrigation_efficiency

            #If irrigation is not yet implemented, pumping costs is 0
            if Irrig.implemented == False:
                pumping_cost_per_Ha = 0
                water_cost_per_Ha = 0
                total_margin = 0 #- irrig_cost_per_Ha+storage_cost_per_Ha
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

                #Is it sensible to include value of unused water?
                total_margin = crop_GM #+ saved_water_value_per_Ha + additional_income
                
            #End if

            total_costs = (irrig_cost_per_Ha+pumping_cost_per_Ha+water_cost_per_Ha+storage_cost_per_Ha) #+ additional_costs #Crop costs already factored in
            negated_profit = total_costs - total_margin

            if Irrig.implemented == True:
                this_max_area = min(Field.area, possible_irrigation_area) #min(possible_irrigation_area, Field.area)
            else:
                #Determine areal costs when irrigation system is not yet implemented
                this_max_area = Field.area 

            #This represents 'c' in LP matrix
            lp_log.set_value(row_id, Field.name+" "+WS.name, negated_profit)

            profits[WS.name] = negated_profit

            max_possible_area += this_max_area

            field_b_ub.append(this_max_area)
            
        #End Water Source loop

        # this_max_area = min(max_possible_area, Field.area)
        # max_area += this_max_area

        #Mark as implemented after first year
        if Irrig.implemented == False:
            Irrig.implemented = True
            field_change = True

        if Store.implemented == False:
            Store.implemented = True
            field_change = True
        #End if

        b_ub.append(this_max_area)

        #Calculate total possible irrigation area
        total_water = sum([WS.entitlement for WS in self.water_sources])
        avg_water_req = sum(water_req)/len(water_req)
        possible_irrigation_area = total_water / avg_water_req

        #Save results for this row
        b_ub_log.loc[row_id] = pd.Series(b_ub)
        b_eq_log.loc[row_id] = pd.Series(b_eq)

        return field_b_ub, field_b_eq, this_max_area, field_change, max_possible_area

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
                pumping_cost_per_Ha = self.Farm.water_sources[water_source_name].calcGrossPumpingCostsPerHa(flow_rate_Lps, est_irrigation_water_ML_per_Ha)

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

    def calcFieldIrrigationDepth(self, Field):
        return Field.calcNetIrrigationDepth(Field)
    #End calcFieldIrrigationDepth()

    def calcGrossIrrigationWaterAmount(self, Field, Crop=None):
        """
        Calculate how much water is needed to be sent out to the fields per Hectare
        Calculations are done in millimeters and then converted to ML.

        See `Estimating Vegetable Crop Water Use (Vic Ag) <http://agriculture.vic.gov.au/agriculture/horticulture/vegetables/vegetable-growing-and-management/estimating-vegetable-crop-water-use/>`_

        Especially Table 4

        .. math::
            NID = D_{rz} * RAW

        where

        * :math:`NID` is Net Irrigation Depth
        * :math:`D_{rz}` is Effective Root Depth (Depth of root zone)
        * :math:`RAW` is Readily Available Water, see calcRAW() method in Soil class

        .. math:: 


        :param Field: Field object
        :returns: Total amount of water to apply in ML
        
        """

        if Crop is None:
            Crop = Field.Crop

        net_irrigation_depth = Field.calcNetIrrigationDepth(Crop.root_depth_m, Crop.depletion_fraction)

        #Check current Soil Water Deficit
        if (Field.c_swd + net_irrigation_depth) >= 0.0 or (Field.c_swd > (0.0-net_irrigation_depth)):
            water_to_send = 0.0
            print "above zero, sending no water"
        else:

            water_application = 0.0 - Field.c_swd

            while (Field.c_swd + water_application) < 0.0:
                water_application = water_application + net_irrigation_depth
            #End while

            #Add again to get it over 0.0 (?)
            #water_application = water_application + net_irrigation_depth

            print water_application
            print 0.0-net_irrigation_depth
            print "here------"

            water_to_send = ((water_application / 100.0) / Field.Irrigation.irrigation_efficiency) * Field.area

            print "water application"
            print water_to_send, water_application, Field.c_swd

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
            recharge = recharge + field.updateCumulativeSWD(ETc[field], gross_water_applied[field])
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

    def calcEffectiveRainfallML(self, rainfall, field_area):

        """
        Calculates effective rainfall, in ML, over the Field area
        """

        e_rainfall = (rainfall - 5.0) if (rainfall - 5.0) > 0.0 else 0.0
        return (e_rainfall / 100) * field_area
    #End calcEffectiveRainfallML()


    def setFieldComponentStatus(self, row):

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

        if row['Irrigation'].irrigation_efficiency >= Field.Irrigation.irrigation_efficiency:
            # row['fields'].WaterSource = row['WaterSource'].getCopy()
            Field.Storage = row['Storage'].getCopy()
            Field.Irrigation = row['Irrigation'].getCopy()
            # row['fields'].Crop = row['Crop'].getCopy()
        else:
            #Non-beneficial change of irrigations, remove from list
            return (np.nan, ) * len(row)

        return row
    #End updateFieldComponents()

    def setupFieldComponentsStatus(self, combinations):

        """
        Set implementation status and remove unneeded combinations for each row in given DataFrame. 
        Each row represents a field combination
        """

        field_combi = {}
        for i, row in combinations.iterrows():
            row = self.setFieldComponentStatus(row)

            if type(row[0]) == float:

                try:
                    if np.isnan(row[0]):
                        continue
                    #End if
                except TypeError as e:
                    import sys; sys.exit(e)
                #End try
            #End if

            field_name = row['fields'].name
            if field_name not in field_combi:
                field_combi[field_name] = []

            field_combi[field_name].append(row['fields'].getCopy())
        #End for

        return field_combi

    #End


    def generateFieldCombinations(self):

        """
        Generate all possible combinations of fields, storages and irrigations
        """

        import itertools

        all_combinations = {
            'fields': [field.getCopy() for field in self.Farm.fields],
            # 'WaterSource': Manager.water_sources[:],
            'Storage': [store.getCopy() for store in self.storages], #self.storages[:],
            'Irrigation': [irrig.getCopy() for irrig in self.irrigations],
            # 'Crop': Manager.crops[:]
        }

        combination_keys = all_combinations.keys()

        #Generate all combinations of available farm components
        all_combinations = [dict(itertools.izip_longest(all_combinations, v)) for v in itertools.product(*all_combinations.values())]

        return pd.DataFrame(all_combinations)

    #End generateFieldCombinations()

    def forwardTraceFieldCombinations(self, years_ahead):

        results = {}

        # for n in xrange(years_ahead)

        pass

        
    

#End FarmManagement()