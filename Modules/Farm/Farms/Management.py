#Management
from __future__ import division
from Modules.Core.IntegratedModelComponent import Component
from Modules.Farm.Fields.Field import FarmField
from Modules.Farm.Fields.Soil import SoilType


import pandas as pd

class FarmManager(Component):

    """
    Farm Manager
    """

    def __init__(self, Farm):

        """
        :param Farm: Farm Object representing the Farm to manage
        """

        self.Farm = Farm
    #End __init__()

    def plantCrops(self, initial_area, soils, timestep):

        """
        Determine what crops to plant

        TODO: Factor in available water
        """

        area_allocation = []
        remaining_area = initial_area
        for crop in self.Farm.crops:
            #Get crop coefficient

            coef = self.Farm.crops[crop].getCurrentStageCoef(timestep)

            if coef != 0.0 and self.Farm.crops[crop].planted != True:

                #Plant the crop
                remaining_area, allocation = self.determineCropAreaToGrow(crop, remaining_area, soils[0])
                area_allocation.append(allocation) 

                #Mark the crop as planted
                self.Farm.crops[crop].planted = True

                if remaining_area == 0.0:
                    break
                #End if

            #End if

        #End for

        return area_allocation, remaining_area


    def determineCropAreaToGrow(self, crop, initial_area, soils=None):

        """
        For the available water and soil type of a field, determine how much area to crop

        Includes dryland and irrigations

        :param crop: crop name as found in Farm.crops
        :param initial_area: available area to irrigate
        :param soils: soil types as found in area

        :returns: list of lists [[irrigation, crop type, area in Hectares]]
        """

        #Optimise input-output

        #WARNING: FOR DEVELOPMENT PURPOSES ONLY
        area_allocation = {}
        available_area = initial_area

        available_area = available_area - (available_area / 2.0)
        area_allocation[crop] = dict(irrigation=self.Farm.irrigations['Flood'], crop=self.Farm.crops[crop], area=available_area, soil=soils)

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

    def calcGrossIrrigationWaterAmount(self, Field):
        """
        Decide how much water to send out to the fields per Hectare

        TODO: Optimisation

        :param Field: Dictionary association of {irrigation, crop, area in hectares}

        :returns: Total amount of water to apply in ML
        
        """

        RAW_mm = Field.soil.calcRAW(fraction=Field.crop.depletion_fraction)
        net_irrigation_depth = Field.crop.root_depth_m * RAW_mm

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

            water_to_send = float(water_application / 100.0) * Field.area
            #water_to_send = Field.crop.water_use_ML_per_Ha * Field.area

        #End if

        return water_to_send

    #End calcGrossIrrigationWaterAmount()

    def calcWaterApplication(self):

        """
        Calculate amount of water to apply to each field

        :returns: Dict of {Field Object: amount of water to apply in ML}
        """

        #Calculate amount of water to apply to each field
        water_to_apply = {}
        for field in self.Farm.fields:
            water_to_apply[field] = self.calcGrossIrrigationWaterAmount(field) #Also need available water?
        #End for

        return water_to_apply

    #End calcWaterApplication()

    def calcCumulativeSWD(self, timestep, timestep_ET, gross_water_applied):

        """
        Calculates Soil Water Deficit within a timestep and updates Field attribute

        :param timestep: Datetime (REMOVE?)
        :param timestep_ET: Average evapotranspiration within given timestep
        :param gross_water_applied: Total water applied to the field in ML

        """


        for field in self.Farm.fields:

            field.c_swd = field.c_swd + ( float((gross_water_applied[field] / field.area) * 100.0) )

            ET_c = timestep_ET * field.crop.getCurrentStageCoef(timestep)
            field.c_swd = field.c_swd - ET_c

        #End field

    #End calcCumulativeSWD()

    def applyWater(self, water_to_apply):

        """
        Applies water to each field under management
        """

        #water_to_apply = self.calcWaterApplication(Fields)

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
    

#End FarmManagement()