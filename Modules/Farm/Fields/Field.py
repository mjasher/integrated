from Modules.Core.IntegratedModelComponent import Component

class FarmField(Component):

    """
    Container to associate an irrigation with a crop type
    """

    def __init__(self, irrigation, crop, soil=None, area=None):
        self.irrigation = irrigation
        self.crop = crop
        self.soil = soil
        self.area = area

        #Cumulative Soil Water Deficit
        self.c_swd = 0

        if self.crop.required_water_ML_per_Ha is None:
            self.crop.required_water_ML_per_Ha = self.irrigation.irrigation_efficiency * self.crop.water_use_ML_per_Ha
        
    #End init()

    def applyWater(self, gross_applied_water_ML):

        """
        Puts water on the field

        :param gross_applied_water_ML: water in ML applied to field
        :returns: (float) water in ML that goes to recharge

        """

        #print "Applied {x} ML on {a} Ha for {c} using {i}".format(x=gross_applied_water_ML, a=self.area, c=self.crop.name, i=self.irrigation.name)

        gross_water_mm = gross_applied_water_ML * 100

        #print "This is calculated to be {g} mm ".format(g=gross_water_mm)

        #get irrigation efficiency
        crop_water_use = gross_applied_water_ML * self.irrigation.irrigation_efficiency
        seepage = gross_applied_water_ML - crop_water_use

        #print "{crop} used: {c}".format(c=crop_water_use, crop=self.crop.name)

        self.crop.updateWaterNeedsSatisfied(crop_water_use, self.area)

        #Update cumulative soil water deficit
        #self.c_swd = self.c_swd + (seepage * 100)

        return seepage

    #End applyWater()

    def applyCropLoss(self):

        """
        Apply losses to crop due to lack of water or other
        
        """

        self.crop.yield_per_Ha = self.crop.yield_per_Ha * self.crop.water_need_satisfied

    #End applyCropLoss()


    def harvest(self):

        """
        Get crop harvest.

        Sets crop area to 0
        
        :returns: Gross crop yield
        """

        harvest = self.crop.yield_per_Ha * self.area

        self.area = 0

        return harvest
    #End harvest()

#End FarmField()