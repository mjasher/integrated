from __future__ import division
from integrated.Modules.Core.IntegratedModelComponent import Component

class FarmField(Component):

    """
    Container to associate an irrigation with a crop, irrigation and storage type
    """

    def __init__(self, name=None, storage=None, irrigation=None, crop=None, soil=None, area=None):
        #self.name = "{i}-{c}".format(i=irrigation.name, c=crop.name)

        """
        :param name: Human readable name of this field
        :param storage: The storage that this field relies on
        :param irrigation: The irrigation installed for this field
        :param crop: The crop planted in this field
        :param soil: Predominant soil type of this field
        :param area: Field area
        """

        if name is None:
            self.name = "{i}-{s}".format(i=irrigation.name, s=soil.name)
        else:
            self.name = name
        #End if

        self.Storage = storage
        self.Irrigation = irrigation
        self.Crop = crop
        self.Soil = soil
        self.area = area
        self.water_applied = 0

        if crop is not None:
            #Cumulative Soil Water Deficit (monitors allowable depletion)
            self.setIniSWD()
        #End if

        #Unused for now
        self.pump_operation_hours = 72*2
        self.pump_operation_days = 3*2
        
    #End init()

    def status(self, timestep):

        return {
            'irrigation': self.Irrigation.name,
            'soil_type': self.Soil.name,
            'soil water deficit': self.c_swd,
            'area': self.area,
            'crop': self.Crop.name,
            'root zone': self.Crop.root_depth_m
            #'nid': self.calcNetIrrigationDepth(timestep)
        }

    #End status()

    def setIniSWD(self):

        """
        Set initial soil water deficit. This is essentially a counter that monitors allowable depletion
        """

        #Cumulative Soil Water Deficit
        self.c_swd = self.Soil.calcRAW(self.Soil.current_TAW_mm, self.Crop.depletion_fraction) - self.Soil.calcRAW(self.Soil.TAW_mm, self.Crop.depletion_fraction) 

        # print "Initial SWD: ", self.c_swd
        # print "Max RAW: ", self.Soil.calcRAW(self.Soil.TAW_mm, self.Crop.depletion_fraction)
        # print "C RAW: ", self.Soil.calcRAW(self.Soil.current_TAW_mm, self.Crop.depletion_fraction)
        # print "TAW: ", self.Soil.TAW_mm
        # print "C TAW: ", self.Soil.current_TAW_mm

        # assert self.c_swd <= 0.0
        assert self.c_swd >= -self.Soil.TAW_mm

        if self.c_swd > 0.0:
            self.c_swd = 0.0
    #End setIniSWD()

    def applyWater(self, gross_applied_water_ML):

        """
        Puts water on the field

        DEPRECATED

        :param gross_applied_water_ML: water in ML applied to field
        :returns: Water in ML that goes to recharge
        :return type: float
        """

        #Calculate crop water use (ETc)
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


    def harvest(self):

        """
        Get crop harvest.
        
        :returns: Gross crop yield
        """

        harvest = self.Crop.yield_per_Ha * self.area

        return harvest
    #End harvest()

    def updateCumulativeSWD(self, gross_water_applied_ML, ETc):

        """
        Follows calculation method outlined in
        http://agriculture.vic.gov.au/agriculture/horticulture/vegetables/vegetable-growing-and-management/estimating-vegetable-crop-water-use

        Calculates the Soil Water Deficit based on the amount of water applied, the crop ET for the timestep, and the crop coefficient for its current growth stage 

        c_swd = c_swd - ETc, ETc = (reference_ET * Crop Coefficient for current stage of development)

        :param timestep_ETc: Crop ET for this timestep (:math:`ETc`) to be multiplied with Crop ET Coefficient for this timestep
        :param gross_water_applied: Gross amount of water applied to the field in ML

        :returns: Total recharge for field in ML

        May have to rethink this cumulative SWD approach.

        K_sat = Max Soil saturation of soil type

        SWD_{i} <= K_sat

        SWD_i = (SWD_{i-1} - ETc) + (Rainfall + Applied Water)

        Recharge = (Rainfall + Applied Water) - (ETc + SWD_{i})

        Simplified version:
        SWD_i = Rainfall + Irrigation - Crop Water Use

        :returns seepage: Seepage/recharge in ML

        Also see "Tindall Method" as in:
        http://www.nt.gov.au/d/Content/File/p/Tech_Bull/TB337.pdf
    
        """

        #mm -> ML = division by 100
        #ML -> mm = multiplication by 100

        assert gross_water_applied_ML >= 0.0, "Water input into soil cannot be less than 0"

        self.c_swd = (self.c_swd - ETc) + ((gross_water_applied_ML * 100) / self.area)

        if self.c_swd > 0.0:

            tmp = (self.c_swd - self.Soil.TAW_mm)

            seepage = tmp if tmp > 0.0 else 0.0
            self.c_swd = 0.0
        else:
            seepage = 0.0
        #End if

        #water_applied_mm_Ha = (gross_water_applied_ML * 100.0 ) / self.area   
        return seepage

    #End calcCumulativeSWD()

    def simpleCropWaterUse(self, water_input):

        cwu = water_input * self.irrigation.irrigation_efficiency

        return {'cwu': cwu, 'recharge': water_input-cwu}
    #End simpleCropWaterUse()

    def calcNetIrrigationDepth(self, timestep, base_irrig_efficiency, val_type='Best Guess', e_rz_coef=0.55):

        """
        Calculate net irrigation depth in mm, subject to irrigation efficiency

        Equation taken from 
        http://agriculture.vic.gov.au/agriculture/horticulture/vegetables/vegetable-growing-and-management/estimating-vegetable-crop-water-use

        See also: \\
        * http://www.fao.org/docrep/x5560e/x5560e03.htm

        * https://www.bae.ncsu.edu/programs/extension/evans/ag452-1.html

        * http://dpipwe.tas.gov.au/Documents/Soil-water_factsheet_14_12_2011a.pdf


        :math:`NID` = Effective root depth (:math:`D_{rz}`) :math:`*` Readily Available Water (:math:`RAW`)

        :math:`NID = D_{rz} * RAW`

        where:

        * :math:`D_{rz}` = :math:`Crop_{root_depth} * Crop_{e_rz}`, where :math:`Crop_{root_depth}` is the estimated root depth for current stage of crop (initial, late, etc.) and :math:`Crop_{e_rz}` is the effective root zone coefficient for the crop. \\
        * :math:`Crop_{e_rz}` is said to be between 1 and 2/3rds of total root depth \\

        * see https://www.agric.wa.gov.au/water-management/calculating-readily-available-water?nopaging=1 \\
          as well as the resources listed above

        * RAW = :math:`p * TAW`, :math:`p` is depletion fraction of crop, :math:`TAW` is Total Available Water in Soil

        As an example, if a crop has a root depth (:math:`RD_{r}`) of 1m, an effective root zone (:math:`RD_{erz}`) coefficient of 0.55, a depletion fraction (p) of 0.4 and the soil has a TAW of 180mm: \\
        :math:`(RD_{r} * RD_{erz}) * (p * TAW)`
        :math:`(1 * 0.55) * (0.4 * 180)`

        """

        crop_depletion_fraction = self.Crop.getCurrentStageDepletionCoef(timestep, val_type)

        # if (self.Crop.root_depth_m * self.Crop.getCurrentStageCropCoef(timestep, val_type)) > self.Crop.root_depth_m:
        #     effective_rz = (self.Crop.root_depth_m * crop_depletion_fraction)
        # else:
        #     effective_rz = (self.Crop.root_depth_m * self.Crop.getCurrentStageCropCoef(timestep, val_type)) * crop_depletion_fraction

        #Effective root zone is roughly half to 2/3rds of root depth
        #https://www.bae.ncsu.edu/programs/extension/evans/ag452-1.html
        #http://dpipwe.tas.gov.au/Documents/Soil-water_factsheet_14_12_2011a.pdf
        #effective_rz = (self.Crop.root_depth_m * crop_depletion_fraction)
        effective_rz = (self.Crop.root_depth_m * e_rz_coef)

        net_irrigation_depth = ( effective_rz * self.Soil.calcRAW(fraction=crop_depletion_fraction))

        #Change net irrigation depth based on irrigation efficiency
        #net_irrigation_depth = net_irrigation_depth * (self.Irrigation.irrigation_efficiency / base_irrig_efficiency)

        assert net_irrigation_depth >= 0.0, "Net irrigation depth will be calculated as above ground!"

        return net_irrigation_depth
    #End calcNetIrrigationDepth()

    # def calcFlowRate_old(self, duration, operational_days, Crop, irrig_efficiency=None):

    #     """
    #     Calculate flow requirements for this field, factoring in crop water requirements

    #     See `this calculator <http://irrigation.wsu.edu/Content/Calculators/Center-Pivot/System-Pumping-Requirements.php>`_ as an example

    #     :param duration: Number of hours available for pump operation per day.
    #     :param operational_days: Number of days the pump will be operated over
    #     :param Crop: Crop object
    #     :param irrig_efficiency: Irrigation Efficiency. Defaults to value set in Irrigation object.

    #     :returns: required flow rate in Litres per second

    #     From Gallons of water
    #     .. math::
    #         Q = (((27154 * Net_{app}) * A) / (60 * (Hrs * Days))) / E

    #     .. math::
    #         Q = ((NID / 100)A / (D*T)) * 1000000 / 60 / 60

    #     where
    #     * :math:`Q` is total flow rate 
    #     * :math:`Net_{app}` is the required application amount per week
    #     * :math:`A` is the area under irrigation
    #     * :math:`Hrs` is the total hours available for pump operation per day
    #     * :math:`Days` is the number of days the pump will be operated over
    #     * :math:`E` is the efficiency of the irrigation system
    #     """

    #     if irrig_efficiency is None:
    #         irrig_efficiency = self.Irrigation.irrigation_efficiency

    #     nid = self.calcNetIrrigationDepth(timestep, Manager.base_irrigation_efficiency)

    #     #total_flow_rate = (((27154 * nid) * self.area) / (60 * (duration * operational_days))) / irrig_efficiency
    #     # total_flow_rate = ((nid * self.area) / (duration * operational_days)) / irrig_efficiency
    #     ML_to_apply = ((nid / 100) * self.area)
    #     ML_per_hour = ML_to_apply / (duration * operational_days) #ML per Hour

    #     total_flow_rate = (((ML_per_hour * 1000000) / 60) / 60) / irrig_efficiency

    #     #Convert from Gallons to Lps
    #     # total_flow_rate = total_flow_rate / 0.0630902

    #     return total_flow_rate
    # #End calcFlowRate_old()

    def calcFlowRate(self, irrigation_flow_capacity=None):

        """
        .. :math:
            Q = (F * 1000000) / 24 / 60 / 60

        where:
        * :math:`Q` is Flow in Litres per second
        * :math:`F` is flow rate in ML per day
        * 1000000 converts :math:`F` from ML to Litres
        * 24 is the hours per day
        * First 60 is the minutes per hour
        * Second 60 is the seconds per minute

        :returns: Flow in Litres per Second
        """

        if irrigation_flow_capacity is None:
            flow_cap = self.Irrigation.flow_ML_day
        else:
            flow_cap = irrigation_flow_capacity
        #End if

        return (flow_cap * 1000000) / 86400 #24 / 60 / 60

    #End calcFlowRate()

    def calcFlowDurationInDays(self, water_to_apply_ML):

        seconds_to_apply = (water_to_apply_ML*1000000) / self.calcFlowRate()
        mins_to_apply = seconds_to_apply / 60 
        hours_to_apply = mins_to_apply / 60
        days_to_apply = mins_to_apply / 24

        return days_to_apply
    #End calcFlowDuration()

    def flowPerIrrigation(self, RAW, area, irrigation_efficiency):

        """
        A method to determine how much water (volume) needed to irrigate a field.
        Need soil Readily Available Water (RAW). area to be irrigated, and efficiency of supply and field application.
        To determine how much water (volume) you need to irrigate your field

        Currently unused as LP determines field area (and is therefore an unknown).

        See page 4 of `this 2002 DPI document <http://www.dpi.nsw.gov.au/__data/assets/pdf_file/0006/176694/surface-irrigation-notes.pdf>`_

        :param nid: Net Irrigation Depth
        :param area: irrigation area
        """

        return (RAW * area) / irrigation_efficiency

    def calcIrrigationArea(self, water_Litres, irrigation_efficiency, RAW):

        """
        If available water volume is known, area that can be irrigated can be determined
        See page 4 of `this DPI document <http://www.dpi.nsw.gov.au/__data/assets/pdf_file/0006/176694/surface-irrigation-notes.pdf>`_
        """

        return (water_Litres * irrigation_efficiency) / RAW

#End FarmField()