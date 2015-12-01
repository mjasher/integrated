from __future__ import division
from integrated.Modules.Core.IntegratedModelComponent import Component

class FarmField(Component):

    """
    Container to associate an irrigation with a crop type
    """

    def __init__(self, irrigation=None, crop=None, soil=None, area=None):
        self.name = "{i}-{c}".format(i=irrigation.name, c=crop.name)
        self.irrigation = irrigation
        self.crop = crop
        self.soil = soil
        self.area = area
        self.water_applied = 0

        #Cumulative Soil Water Deficit
        self.c_swd = self.soil.calcRAW(self.soil.TAW_mm, self.crop.depletion_fraction) - self.soil.calcRAW(self.soil.current_TAW_mm, self.crop.depletion_fraction)
        #self.soil.TAW_mm - self.soil.current_TAW_mm

        if self.crop.required_water_ML_per_Ha is None:
            self.crop.required_water_ML_per_Ha = self.irrigation.irrigation_efficiency * self.crop.water_use_ML_per_Ha
        
    #End init()

    def status(self):

        return {
            'irrigation': self.irrigation.name,
            'soil_type': self.soil.name,
            'soil water deficit': self.c_swd,
            'area': self.area,
            'crop': self.crop.name,
            'root zone': self.crop.root_depth_m
        }

    #End status()


    def applyWater(self, gross_applied_water_ML):

        """
        Puts water on the field

        :param gross_applied_water_ML: water in ML applied to field
        :returns: Water in ML that goes to recharge
        :return type: float
        """

        #Calculate crop water use (ET_c)
        crop_water_use = gross_applied_water_ML * self.irrigation.irrigation_efficiency
        seepage = gross_applied_water_ML - crop_water_use

        self.crop.updateWaterNeedsSatisfied(crop_water_use, self.area)

        return seepage

    #End applyWater()

    def applyCropLoss(self):

        """
        Apply losses to crop due to lack of water or other
        
        """

        #self.crop.yield_per_Ha = self.crop.yield_per_Ha * self.crop.water_need_satisfied

        pass

    #End applyCropLoss()


    def harvest(self):

        """
        Get crop harvest.

        Sets crop area to 0
        
        :returns: Gross crop yield
        """

        harvest = self.crop.yield_per_Ha * self.area

        return harvest
    #End harvest()

    def updateCumulativeSWD(self, timestep, timestep_ETc, gross_water_applied):

        """
        Follows calculation method outlined in
        http://agriculture.vic.gov.au/agriculture/horticulture/vegetables/vegetable-growing-and-management/estimating-vegetable-crop-water-use

        Calculates the Soil Water Deficit based on the amount of water applied, the crop ET for the timestep, and the crop coefficient for its current growth stage 

        c_swd = c_swd - ET_c, ET_c = reference_ET * Crop ET Coefficient for current stage of development

        :param timestep: Current Timestep (date) [UNUSED]
        :param timestep_ETc: Crop ET for this timestep (:math:ETc) to be multiplied with Crop ET Coefficient for this timestep
        :param gross_water_applied: Gross amount of water applied to the field in ML

        :returns: Total recharge for field

        """

        """
        Have to rethink this cumulative SWD approach.


        K_sat = Max Soil saturation of soil type

        SWD_i <= K_sat

        SWD = (SWD_i - ETc) + (Rainfall + Applied Water)

        Recharge = (Rainfall + Applied Water) - (ETc + SWD_i)

        Simplified version:
        SWD_i = Rainfall + Irrigation - Crop Water Use
    
        """

        #mm -> ML = division by 100
        #ML -> mm = multiplication by 100

        #Divide by 100 to convert Total ML into mm/Ha
        self.c_swd = self.c_swd + ( ( (gross_water_applied * 100.0) / self.area) - ((timestep_ETc*100) / self.area) )

        #self.c_swd = (self.c_swd - timestep_ETc) + ((gross_water_applied / self.area) * 100.0) #multiplied by 100 to convert to millimetres

        if self.c_swd > 0.0:

            seepage = 0.0

            if self.soil.current_TAW_mm < self.soil.TAW_mm:
                if (self.soil.current_TAW_mm + self.c_swd) > self.soil.TAW_mm:
                    seepage = (self.soil.current_TAW_mm + self.c_swd) - self.c_swd
                    self.soil.current_TAW_mm = self.soil.TAW_mm
                else:
                    self.soil.current_TAW_mm = self.soil.current_TAW_mm + self.c_swd
                    seepage = self.c_swd
            
            self.c_swd = 0.0

            seepage = (seepage / 100) #ML per Hectare
        else:
            seepage = 0.0
            
        return seepage

    #End calcCumulativeSWD()

    def simpleCropWaterUse(self, water_input):

        cwu = water_input * self.irrigation.irrigation_efficiency

        return {'cwu': cwu, 'recharge': water_input-cwu}
    #End simpleCropWaterUse()


#End FarmField()