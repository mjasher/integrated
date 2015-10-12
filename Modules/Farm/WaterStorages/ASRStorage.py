from BasinStorage import BasinStorage
#from Common.GeneralFunctions import *

class ASRStorage(BasinStorage):

    """
    Defines MAR with injection, a type of Basin storage
    """

    def __init__(self, **kwargs):

        """
        ASR Storage system (Injection)

        ASR Specific variables

        cost_temp_storage_per_ML
        cost_treatment_capital_cost
        cost_treatment_per_ML
        cost_of_design
        cost_of_design_as_proportion_of_capital

        See BasinStorage class
        """

        BasinStorage.__init__(self, **kwargs)

        #Set up derived parameters
        self.net_water_available = self.WaterSources.calcGrossWaterAvailable() - (self.MAR_loss_rate * self.MAR_ML)
        self.updatePumpVolML()

        self.capture_pump_cost_dollar_per_ML = self.calcCapturePumpCostPerML()

        self.annual_cost = self.calcAnnualCosts()

        self.cost_capital = 0

    #End init()

    def calcDesignCosts(self):

        #design_cost = (self.cost_capital + self.capital_cost_treatment) * self.cost_of_design_as_proportion_of_capital
        design_cost = (0 + self.calcCapitalCostTreatment()) * self.cost_of_design_as_proportion_of_capital

        return design_cost
    #End calcDesignCost()

    def calcCapturePumpCostPerML(self):

        return self.pump_cost_dollar_per_ML * self.capture_pump_cost_ratio


    def calcCapitalCostTreatment(self):

        self.capital_cost_treatment = self.capital_cost_treatment_per_ML * self.storage_capacity_ML

        return self.capital_cost_treatment

    #End calcCapitalCostTreatment()

    def calcSurfacePumpCost(self, total_surface_water):

        surface_pump_cost = total_surface_water * self.calcCapturePumpCostPerML()

        return surface_pump_cost
    #End calcSurfacePumpCost()

    def calcOngoingCosts(self):

        #pump_cost = self.pump_vol_ML * self.pump_cost_dollar_per_ML

        maintenance_cost = self.maintenance_rate  * (self.cost_capital + self.capital_cost_treatment)
        pump_cost = self.calcPumpCost(self.pump_vol_ML)

        surface_pump_cost = self.calcSurfacePumpCost(self.WaterSources.water_source['flood_harvest'])

        return (self.cost_treatment_per_ML * self.MAR_ML) + maintenance_cost + pump_cost + surface_pump_cost
    #End calcOngoingCosts()

    def calcTotalCapitalCosts(self):

        #From parent class
        temp_storage_cost = self.calcTemporaryStorageCosts()
        capital_cost = self.calcDesignCosts() + self.cost_capital + self.capital_cost_treatment + temp_storage_cost

        #storage_capital_cost = self.calcStorageCapitalCostPerML(self.capital_cost_per_ML_at_02_per_day) * self.storage_capacity_ML
        #storage_capital_cost = capital_cost * self.storage_capacity_ML
        #self.capital_cost = 0 #capital.cost is 0 in original code.

        #capital_cost = self.calcDesignCosts() + self.calcStorageCapitalCosts() + self.calcTemporaryStorageCosts()
        return capital_cost

    #End calcCapitalCosts()

    def calcAnnualCosts(self):

        #total_surface_water = self.WaterSources.water_source['flood_harvest']

        capital_cost = self.calcTotalCapitalCosts()
        
        ongoing_cost = self.calcOngoingCosts()
        cost = calcCapitalCostPerYear(capital_cost, self.discount_rate, self.num_years) + ongoing_cost

        #cost = cost + net_environmental_cost

        #Debugging, comparing to original code
        # print "Number of Years: "+str(self.num_years)
        # print "Storage Capacity: "+str(self.storage_capacity_ML)
        # print "Capital Cost per ML: "+str(self.capital_cost_per_ML) + " | Should be: 700"
        # print "Capital cost of Treatment per ML: "+str(self.capital_cost_treatment_per_ML)+ "| Should be: 250"
        # print "Cost of Treatment (NOT capital cost) per ML: "+str(self.cost_treatment_per_ML)+ "| Should be: 150"
        # print "Storage capital cost: "+str(self.cost_capital)+" | Should be: 0"
        # print "Calc capital cost: "+str(capital_cost)+" | Should be: 55000"
        # print "Discount Rate: "+str(self.discount_rate)+" | Should be: 0.07"
        # print "Number of Years: "+str(self.num_years)+" | Should be: 25"
        # print "Pump Cost: "+str(pump_cost)+" | Should be: 6650"
        # print "Design Cost: "+str( self.calcDesignCosts() )+" | Should be: 5000"
        # print "Storage Capital Cost: "+str(storage_capital_cost)+" | Should be: 0"
        # print "Treatment Capital Cost: "+str(self.capital_cost_treatment) + " | should be: 50000"
        # print "Temp Storage Cost: "+str(temp_storage_cost)+" | should be: 0"
        # print "Maintenance Rate: "+str(self.maintenance_rate)+ " | should be 0.07"
        # print "Maintenance Cost: "+str(maintenance_cost)+ " | should be 3500"
        # print "--------------------------------"
        # print "Ongoing Cost: "+str(ongoing_cost)+ "| should be: 44350"
        # print "Annual Cost: "+str(cost)+" | Should be: 49541.61"

        self.annual_cost = cost

        return cost

    #End calcAnnualCosts()

#End class
