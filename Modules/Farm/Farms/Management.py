#Management
from __future__ import division
from integrated.Modules.Core.IntegratedModelComponent import Component
from integrated.Modules.Farm.Fields.Field import FarmField
from integrated.Modules.Farm.Fields.Soil import SoilType
from integrated.Modules.Farm.Irrigations.IrrigationPractice import IrrigationPractice

#remove this when ready
from random import randint

import pandas as pd

class FarmManager(Component):

    """
    Farm Manager
    """

    def __init__(self, Farm, ):

        """
        :param Farm: Farm Object representing the Farm to manage
        """

        self.Farm = Farm

    #End __init__()

    def plantCrops(self, initial_area, soils, timestep):

        """
        Determine what crops to plant

        TODO: Factor in available water, crop water use efficiencies, etc.
        CURRENTLY USING RANDOM SOIL/CROP TYPE FOR DEVELOPMENT
        """

        area_allocation = []
        remaining_area = initial_area
        for crop in self.Farm.crops:

            #Get crop coefficient
            coef = self.Farm.crops[crop].getCurrentStageCoef(timestep)

            if coef != 0.0 and self.Farm.crops[crop].planted != True:

                #WARNING
                #Random soil type for dev purposes
                num = len(soils)
                crop_num = randint(0, num-1)

                #Plant the crop
                remaining_area, allocation = self.determineCropAreaToGrow(crop, remaining_area, soils[crop_num])
                area_allocation.append(allocation) 

                #Mark the crop as planted
                self.Farm.crops[crop].planted = True

                if remaining_area == 0.0:
                    break
                #End if

            #End if

        #End for

        return area_allocation, remaining_area


    def determineCropAreaToGrow(self, crop, initial_area, soil=None):

        """
        For the available water and soil type of a field, determine how much area to crop

        Includes dryland and irrigations
        WARNING: CURRENTLY USES VALUES FOR DEVELOPMENT PURPOSES ONLY
        TODO: LP Optimisation

        :param crop: crop name as found in Farm.crops
        :param initial_area: available area to irrigate
        :param soil: Dominant soil type found in area

        :returns: list of lists [[irrigation, crop type, area in Hectares]]
        """

        #Optimise input-output

        #WARNING: FOR DEVELOPMENT PURPOSES ONLY
        area_allocation = {}
        available_area = initial_area

        available_area = available_area - (available_area / 2.0)
        area_allocation[crop] = dict(irrigation=IrrigationPractice(**self.Farm.irrigations['Flood'].getParams()), crop=self.Farm.crops[crop], area=available_area, soil=soil)

        self.Farm.fields.append(FarmField(irrigation=area_allocation[crop]['irrigation'], crop=area_allocation[crop]['crop'], area=area_allocation[crop]['area'], soil=area_allocation[crop]['soil']))

        return available_area, area_allocation

    #End determineCropAreaToGrow()

    def determineFieldSize(self):

        """
        Does nothing. Remove?
        """

        #Do optimisation?

        return 100.0
    #End determineFieldSize()

    def calcNetIrrigationDepth(self, Field):

        RAW_mm = Field.soil.calcRAW(fraction=Field.crop.depletion_fraction)
        net_irrigation_depth = Field.crop.root_depth_m * RAW_mm

        return net_irrigation_depth
    #End calcNetIrrigationDepth()

    def calcGrossIrrigationWaterAmount(self, Field):
        """
        Calculate how much water is needed to be sent out to the fields per Hectare
        Calculations are done in millimeters and then converted to ML.

        See:
        http://agriculture.vic.gov.au/agriculture/horticulture/vegetables/vegetable-growing-and-management/estimating-vegetable-crop-water-use
        Especially Table 4

        TODO: Optimisation

        :math:`NID = D_{rz} * RAW`, where
        * :math:`NID` is Net Irrigation Depth
        * :math:`D_{rz}` is Effective Root Depth (Depth of root zone)
        * :math:`RAW` is Readily Available Water, see calcRAW() method in Soil class

        :param Field: Dictionary association of {irrigation, crop, area in hectares}

        :returns: Total amount of water to apply in ML
        
        """

        net_irrigation_depth = self.calcNetIrrigationDepth(Field)

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
        for field in self.Farm.fields:
            water_to_apply[field] = self.calcGrossIrrigationWaterAmount(field)
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

    def calcPotentialCropYield(self, ssm_mm, gsr_mm, evap_mm_coef, wue_mm_coef):

        """
        Uses French-Schultz equation 

        TODO: Adapt modified version of French-Schultz from
        http://www.regional.org.au/au/asa/2008/concurrent/assessing-yield-potential/5827_oliverym.htm

        Represents Readily Available Water - (Crop evapotranspiration * Crop Water Use Efficiency Coefficient)

        :math:`YP = (SSM + GSR) - (E * WUE)`, where

        * :math:`YP` is yield potential in kg/Ha 
        * :math:`SSM` is Stored Soil Moisture in mm
        * :math:`GSR` is Growing Season Rainfall in mm
        * :math:`E` is Crop Evaporation coefficient in mm
        * :math:`WUE` is Water Use Efficiency coefficient in kg/mm

        :param ssm_mm: Stored Soil Moisture (mm)
        :param gsr_mm: Growing Season Rainfall (mm)
        :param evap_mm_coef: Crop Evaporation coefficient (mm)
        :param wue_mm_coef: Water Use Efficiency coefficient (kg/mm)

        :returns: Potential yield in kg/Ha

        """

        return (ssm_mm + gsr_mm) - (evap_mm_coef * wue_mm_coef)

    #End calcPotentialCropYield()
    

#End FarmManagement()