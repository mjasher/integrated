from __future__ import division
from integrated.Modules.Core.IntegratedModelComponent import Component

class FarmField(Component):

    """
    Container to associate an irrigation with a crop type
    """

    def __init__(self, name=None, irrigation=None, crop=None, soil=None, area=None):
        #self.name = "{i}-{c}".format(i=irrigation.name, c=crop.name)

        if name is None:
            self.name = "{i}-{s}".format(i=irrigation.name, s=soil.name)
        else:
            self.name = name
        #End if

        self.Irrigation = irrigation
        self.Crop = crop
        self.Soil = soil
        self.area = area
        self.water_applied = 0

        if crop is not None:
            #Cumulative Soil Water Deficit
            self.c_swd = self.Soil.calcRAW(self.Soil.TAW_mm, self.Crop.depletion_fraction) - self.Soil.calcRAW(self.Soil.current_TAW_mm, self.Crop.depletion_fraction)
            #self.Soil.TAW_mm - self.Soil.current_TAW_mm

            if self.Crop.required_water_ML_per_Ha is None:
                self.Crop.required_water_ML_per_Ha = self.Irrigation.irrigation_efficiency * self.Crop.water_use_ML_per_Ha
            #End if
        #End if

        self.pump_operation_hours = 72*2
        self.pump_operation_days = 3*2
        
    #End init()

    def status(self):

        return {
            'irrigation': self.irrigation.name,
            'soil_type': self.Soil.name,
            'soil water deficit': self.c_swd,
            'area': self.area,
            'crop': self.Crop.name,
            'root zone': self.Crop.root_depth_m
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

        self.Crop.updateWaterNeedsSatisfied(crop_water_use, self.area)

        return seepage

    #End applyWater()

    def applyCropLoss(self):

        """
        Apply losses to crop due to lack of water or other
        
        """

        #self.Crop.yield_per_Ha = self.Crop.yield_per_Ha * self.Crop.water_need_satisfied

        pass

    #End applyCropLoss()


    def harvest(self, ):

        """
        Get crop harvest.
        
        :returns: Gross crop yield
        """

        harvest = self.Crop.yield_per_Ha * self.area

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

        May have to rethink this cumulative SWD approach.

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

        if self.c_swd > 0.0:

            seepage = 0.0

            if self.Soil.current_TAW_mm < self.Soil.TAW_mm:
                if (self.Soil.current_TAW_mm + self.c_swd) > self.Soil.TAW_mm:
                    seepage = (self.Soil.current_TAW_mm + self.c_swd) - self.c_swd
                    self.Soil.current_TAW_mm = self.Soil.TAW_mm
                else:
                    self.Soil.current_TAW_mm = self.Soil.current_TAW_mm + self.c_swd
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

    def calcNetIrrigationDepth(self, crop_root_depth_m, crop_depletion_fraction):

        """
        Calculate net irrigation depth in mm
        """

        RAW_mm = self.Soil.calcRAW(fraction=crop_depletion_fraction)
        net_irrigation_depth = crop_root_depth_m * RAW_mm

        return net_irrigation_depth
    #End calcNetIrrigationDepth()

    def calcFlowRate(self, duration, operational_days, Crop, irrig_efficiency=None):

        """
        Calculate flow requirements for this field, factoring in crop water requirements

        See `this calculator <http://irrigation.wsu.edu/Content/Calculators/Center-Pivot/System-Pumping-Requirements.php>`_

        Calculates gallons per minute and converts to Litres per second

        :param duration: Number of hours available for pump operation per day.
        :param operational_days: Number of days the pump will be operated over
        :param Crop: Crop object
        :param irrig_efficiency: Irrigation Efficiency. Defaults to value set in Irrigation object.

        :returns: required flow rate in Litres per second

        .. :math:
            Q = (((27154 * Net_{app}) * A) / (60 * (Hrs * Days))) / E

        where
        * :math:`Q` is total flow rate 
        * :math:`Net_{app}` is the required application amount per week
        * :math:`A` is the area under irrigation
        * :math:`Hrs` is the total hours available for pump operation per day
        * :math:`Days` is the number of days the pump will be operated over
        * :math:`E` is the efficiency of the irrigation system
        """

        if irrig_efficiency is None:
            irrig_efficiency = self.Irrigation.irrigation_efficiency

        nid = self.calcNetIrrigationDepth(Crop.root_depth_m, Crop.depletion_fraction)
        total_flow_rate = (((27154 * nid) * self.area) / (60 * (duration * operational_days))) / irrig_efficiency

        #Convert to Lps
        total_flow_rate = total_flow_rate / 0.0630902

        return total_flow_rate
    #End calcFlowRate()

#End FarmField()