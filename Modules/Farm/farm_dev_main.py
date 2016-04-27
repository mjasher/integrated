from __future__ import division

from integrated.Modules.WaterSources.SurfaceWater import SurfaceWaterSource
from integrated.Modules.WaterSources.Groundwater import GroundwaterSource

import integrated.Modules.Farm.setup_dev as FarmConfig
from integrated.Modules.Farm.Farms.FarmInfo import FarmInfo
from integrated.Modules.Farm.Management.Manager import FarmManager
from integrated.Modules.Farm.Management.Finance import FarmFinance
from integrated.Modules.Farm.Fields.Field import FarmField
from integrated.Modules.Farm.Fields.Soil import SoilType
from integrated.Modules.Farm.Crops.CropInfo import CropInfo
from integrated.Modules.Core.Handlers.FileHandler import FileHandler
#from integrated.Modules.Core.Handlers.BOMHandler import BOMHandler

from scipy.optimize import linprog as lp
import datetime
import pandas as pd
import numpy as np

DEBUG = False

# from scipy.optimize import linprog as lp

# c = [-500, -400, -600, -350]
# A_ub = [[1, 1, 0, 0], [0, 0, 1, 1]]
# b_ub = [50, 45]
# bounds = ((0, 95), ) * 4

# x = lp(c=c, A_ub=A_ub, b_ub=b_ub, bounds=bounds)

# print x

def memoFieldCombinations(row, func, Manager, c_log, b_ub_log, b_eq_log, b_ub_memo={}, comp_memo={}):

    """
    Decorator method to allow memoization for generating Linear Programming coefficients and constraints

    """

    WaterSources = Manager.Farm.water_sources

    try:
        row_id = row[0]
    except IndexError:
        row_id = 0

    max_area = []
    b_ub = b_ub_log
    
    b_eq = []

    #For determining average water requirements
    water_req = []

    field_change = False
    for Field in row[1:]:
        if type(Field) is not FarmField:
            continue
        #End if

        implementation_change = False

        Store = Field.Storage
        Irrig = Field.Irrigation

        Field.Crop.planted = True

        field_store = Field.name+" "+Store.name
        if field_store in comp_memo:
            storage_cost_per_Ha = comp_memo[field_store]
        else:
            #Calculate storage costs and memoize
            storage_cost_per_Ha = Manager.calcStorageCostsPerHa(Field)

            if Store.implemented is True:
                comp_memo[field_store] = storage_cost_per_Ha
            #End if
        #End if

        field_irrig = Field.name+" "+Irrig.name
        if field_irrig in comp_memo:
            irrig_cost_per_Ha = comp_memo[field_irrig]
        else:
            
            #Includes implementation cost if necessary
            irrig_cost_per_Ha = Irrig.calcTotalCostsPerHa()

            if Irrig.implemented is True:
                comp_memo[field_irrig] = irrig_cost_per_Ha
            #End if
        #End if

        logs = [
            b_ub,
            b_eq,
            c_log,
            water_req,
            max_area
        ]

        field_change = func(row_id, Field, WaterSources, storage_cost_per_Ha, irrig_cost_per_Ha, logs, field_change)

        Field.Crop.planted = False
        Field.Crop.plant_date = None

    #End field loop

    #Calculate total possible irrigation area
    total_water = sum([WS.allocation for WS in Manager.Farm.water_sources])
    avg_water_req = sum(water_req)/len(water_req)
    possible_irrigation_area = total_water / avg_water_req

    try:
        total_area = sum(max_area)

        if field_change is False:
            c_log.set_value(row_id, 'bounds', (0, min(possible_irrigation_area, total_area)))
        else:
            c_log.set_value(row_id, 'bounds', (0, total_area) )
        #End if

        c_log.set_value(row_id, 'max_area', total_area)

    except ValueError as e:
        print c_log
        import sys; sys.exit(e)
    #End try

    return row

#End memoFieldCombinations()

if __name__ == "__main__":
    import datetime
    import pandas as pd
    import numpy as np
    from integrated.Modules.Climate.ClimateVariables import Climate
    from integrated.Modules.Farm.WaterStorages.FarmDam import FarmDam
    from integrated.Modules.Farm.Management.LpInterface import LpInterface

    from integrated.Modules.WaterSources.SurfaceWater import SurfaceWaterSource
    from integrated.Modules.WaterSources.Groundwater import GroundwaterSource

    import integrated.Modules.Farm.setup_dev as FarmConfig
    from integrated.Modules.Farm.Farms.FarmInfo import FarmInfo
    from integrated.Modules.Farm.Management.Manager import FarmManager
    from integrated.Modules.Farm.Management.Finance import FarmFinance
    from integrated.Modules.Farm.Fields.Field import FarmField
    from integrated.Modules.Farm.Fields.Soil import SoilType
    from integrated.Modules.Farm.Crops.CropInfo import CropInfo
    from integrated.Modules.Core.Handlers.FileHandler import FileHandler

    #Tired of having columns split over several lines
    pd.set_option('max_colwidth', 5000)
    pd.set_option('display.width', 5000)

    TestFarm = FarmInfo(**FarmConfig.BASE_FARM.getParams())

    print "Processing {farm_name}".format(farm_name=TestFarm.name)
    print "--------------------------"

    print "Setting up historical data for Echuca area"
    print "--------------------------"

    #Real data for Echuca
    ClimateData = FileHandler().loadCSV('test_data/climate/climate.csv', columns=['Date', '406265_rain', '406265_evap'], index_col=0, dayfirst=True, parse_dates=True)
    ClimateData.index.name = 'Date'
    ClimateData.columns = ['rainfall', 'ET']

    Climate = Climate()

    water_sources = [
        #http://www.g-mwater.com.au/downloads/gmw/Pricing_Table_June15.pdf

        #Bulk water, high reliability fee = 24.86
        #Entitlement Storage fee = 10.57

        # Water District
        # East Loddon (North)
        # Service: 100
        # Water Allowance Storage 8.16 / ML
        # ...

        #Diversion fees
        #Annual fee: $100 (account fee) + $100 (service point fee) + $2.04 per ML (access fee)

        #Groundwater entitlement is an average of total licence volume / number of licences in Echuca.
        #Average across entire lower Campaspe is ~407ML
        #see http://www.g-mwater.com.au/downloads/gmw/Groundwater/Lower_Campaspe_Valley_WSPA/Nov_2013_-_Lower_Campaspe_Valley_WSPA_Plan_A4_FINAL-fixed_for_web.pdf
        # esp. Section 2.2 (Groundwater Use) page 8, 

        #Groundwater fees: http://www.g-mwater.com.au/downloads/gmw/Forms_Groundwater/2015/TATDOC-2264638-2015-16_Schedule_of_Fees_and_Charges_-_Groundwater_and_Bore_Construction.pdf
        #Service fee per licence: $100
        #Access fee per service point: $100
        #Resource management fee: $2.53 per ML
        #overuse fee: $2000 per ML

        #Other 
        #Bore Construction fee: $1440
        #Replacement bore: $900
        #Each Additional bore: $170
        #licence amendment: $527 (alter number of bores, alter depth of bore, change bore site)

        #TODO: Need to add static, yearly costs
        SurfaceWaterSource(name='Surface Water', water_level=0, entitlement=100.0, water_value_per_ML=150, cost_per_ML=24.86+10.57),
        GroundwaterSource(name='Groundwater', water_level=4, entitlement=364.0, water_value_per_ML=150, cost_per_ML=2.53)
    ]

    storages = [FarmDam(**FarmConfig.FarmDam_params.getParams())]
    #irrigations = [FarmConfig.PipeAndRiser.getCopy(), FarmConfig.Spray.getCopy(), FarmConfig.Flood.getCopy(), FarmConfig.Dryland.getCopy()]
    irrigations = [FarmConfig.Spray.getCopy()] #FarmConfig.Spray.getCopy(), FarmConfig.Dryland.getCopy()

    #crops = [CropInfo(**cp.getParams()) for crop_name, cp in FarmConfig.crop_params.iteritems()]
    crops = [CropInfo(**FarmConfig.crop_params['Irrigated Winter Wheat'].getParams()), \
             CropInfo(**FarmConfig.crop_params['Dryland Winter Wheat'].getParams()), \
             CropInfo(**FarmConfig.crop_params['Irrigated Winter Barley'].getParams()),]

    crops = [CropInfo(**FarmConfig.crop_params['Irrigated Winter Wheat'].getParams()), \
             CropInfo(**FarmConfig.crop_params['Dryland Winter Wheat'].getParams())]


    FileHandler = FileHandler()
    LpInterface = LpInterface()
    Finance = FarmFinance()
    Manager = FarmManager(TestFarm, water_sources, storages, irrigations, crops, LpInterface, Finance)
    Manager.base_irrigation_efficiency = FarmConfig.Flood.getCopy().irrigation_efficiency

    #Some useful data values may be found in the below
    #See Table 2, Echuca:
    #http://www.g-mwater.com.au/downloads/gmw/Groundwater/Lower_Campaspe_Valley_WSPA/30_Sept_2015-LOWER_CAMPASPE_VALLEY_WSPA_ANNUAL_REPORT_-_2014_15_-_SIGNED.pdf

    Manager.Farm.storages = {'Farm Dam': FarmDam(**FarmConfig.FarmDam_params.getParams())}

    FarmDam = FarmDam(**FarmConfig.FarmDam_params.getParams())

    fields = [
        FarmField(name='Field A', irrigation=FarmConfig.Spray.getCopy(), area=70, storage=FarmDam.getCopy(), soil=SoilType(**FarmConfig.Loam_params.getParams())),
        # FarmField(name='Field A', irrigation=FarmConfig.Flood.getCopy(), area=88, storage=FarmDam.getCopy(), soil=SoilType(**FarmConfig.Loam_params.getParams())),
        FarmField(name='Field B', irrigation=FarmConfig.Spray.getCopy(), area=40, storage=FarmDam.getCopy(), soil=SoilType(**FarmConfig.Light_clay_params.getParams())),
        # FarmField(name='Field C', irrigation=FarmConfig.PipeAndRiser.getCopy(), area=10, storage=FarmDam.getCopy(), soil=SoilType(**FarmConfig.Clay_loam_params.getParams())),
        # FarmField(name='Field D', irrigation=FarmConfig.Spray.getCopy(), area=10, storage=FarmDam.getCopy(), soil=SoilType(**FarmConfig.Clay_loam_params.getParams()))
    ]

    Manager.Farm.fields = [field.getCopy() for field in fields]
    Manager.Farm.water_sources = [ws.getCopy() for ws in Manager.water_sources]

    #Generate all combinations
    field_combinations = Manager.generateFieldCombinations()

    orig_field_combinations = field_combinations.copy()

    #field_combinations['area_breakdown'] = 0
    #A_ub = Manager.LpInterface.genAllAubs(orig_field_combinations, Manager.crops, Manager.water_sources)

    years_ahead = 20
    field_results_memo = {}
    b_ub_memo = {}

    #Manager.LpInterface.setLogTemplates(field_combinations)
    crop_rotations = Manager.crop_rotations.copy()

    #FIRST PHASE, SIMPLISTIC LP RUN TO DETERMINE 'BEST'
    #TODO:
    #  Implement assumed change of crops over years in response to climate/price/water
    #
    results = {}
    for n in xrange(years_ahead):

        c_log, b_ub_log, b_eq_log = Manager.LpInterface.genLogTemplates(field_combinations)

        # Use of apply() causes the first row to be run twice; problematic when the irrigation system has not been implemented 
        # so use a traditional loop instead, even though it is slower
        for row in field_combinations.itertuples():
            #Calculate results for the given combinations
            row = memoFieldCombinations(row, Manager.calcFieldCombination, Manager, c_log, b_ub_log, b_eq_log)
        #End for

        A_ub = Manager.LpInterface.genAubs(c_log, Manager.Farm.water_sources)

        lp_results = Manager.LpInterface.runLP(None, c_log, A_ub, b_ub_log, b_eq_log, field_combinations, Manager.Farm.water_sources)

        #Replace field objects with names
        results[n] = pd.DataFrame(columns=lp_results.columns)
        results[n].index.name = 'Combination ID'
        for i in lp_results.index:

            cols = lp_results.columns
            for col_name in cols:

                obj = lp_results.loc[i, col_name]

                if type(obj) is FarmField:
                    val = "{F} {S} {i} {c}".format(F=obj.name, S=obj.Storage.name, i=obj.Irrigation.name, c=obj.Crop.name) #, WS=obj.WaterSource.name
                else:
                    val = lp_results.loc[i, col_name]
                #End if

                results[n].set_value(i, col_name, val)
            #End for
        #End for

        try:
            results[n]['total_profit'] = results[n-1]['total_profit'] + (results[n]['profit'] * -1)
        except KeyError:
            results[n]['total_profit'] = results[n]['profit'] * -1

            #Add incentive or other in first year
            results[n]['total_profit'] = results[n]['total_profit'] #- 392200

        results[n]['annualised'] = Manager.Finance.annualizeCapital(results[n]['total_profit'], num_years=n+1)

        #Save results
        # FileHandler.writeCSV(results[n], 'output', 'dp_lp_{n}.csv'.format(n=n+1))

        print "======= End of Year {n} ======".format(n=n+1)

    #End years ahead loop

    #Get best performing configuration
    best_field_config_index = results[n]['total_profit'].idxmax()

    Manager.Farm.fields = orig_field_combinations.iloc[best_field_config_index].tolist()

    print "Best Field Setup: "
    for Field in Manager.Farm.fields:
        print Field.name
        print "  Storage: "+Field.Storage.name
        print "  Irrigation: "+Field.Irrigation.name
        Field.Crop.planted = False
        Field.Crop.plant_date = None
        Field.setIniSWD()

        print "  Planted? ", Field.Crop.planted
        print "  Plant Date: ", Field.Crop.plant_date
    #End for
    
    #Rerun using observed data

    start_date = datetime.date(year=1950, month=5, day=20)
    end_date = datetime.date(year=1988, month=5, day=19)
    timestep = datetime.date(year=1950, month=5, day=20)

    #TODO:
    #  Implement observed changes over years
    #  Manager.setupSeason() <- choose suitable crops
    #  Each timestep, LP the most suitable water source
    #    Generate the 'A_ub' and 'b_ub' once
    #    Generate 'c' each step if irrigations are implemented
    #    Remember, irrigations are not implemented until end of season...
    #
    step = 7 #days for each timestep
    step_ahead = datetime.timedelta(days=step)

    #TODO: RUN 2ND STEP FOR EACH FIELD COMBINATION
    """
    for field_combi in orig_field_combinations.itertuples():
        Manager.Farm.fields = list(field_combi)[1:]

        #While loop here

    """
    #Manager.Farm.fields = orig_field_combinations.iloc[best_field_config_index].tolist()
    #results_obs = pd.DataFrame(c_log[c_log.index == 0].copy())
    results_obs = None

    pumping_costs = 0
    total_effective_rainfall = {}
    total_water_applied = {}

    long_results = {}
    irrigation_log = {}
    season_counter = 0 #debugging counter

    year_counter = 1 #Count number of years to annualise profits
    print "---- Starting long loop ----"
    while timestep < end_date:

        #End date of current timestep
        loop_timestep = timestep + step_ahead

        current_ts = pd.to_datetime(timestep)

        if DEBUG:
            #Show end date of timestep
            print "--- Start time step {s}-{e} ---\n".format(s=timestep, e=loop_timestep)
        #End if
        
        timestep_mask = (ClimateData.index >= str(timestep)) & (ClimateData.index < str(loop_timestep))

        #Get ETo for past month
        timestep_ETo = ClimateData.ET[timestep_mask].sum()

        #Sum of rainfall that occured in this timestep
        total_timestep_rainfall = ClimateData.rainfall[timestep_mask].sum()
        timestep_rainfall = ClimateData.rainfall[timestep_mask].copy()
        num_rainfall_events = (ClimateData.rainfall[timestep_mask] > 0).sum()

        total_field_area = 0
        timestep_pumping_cost = 0

        #TODO 
        #  LP to run once every timestep to determine areal proportion to be watered by each water source  

        if (Manager.season_started == False) and (current_ts >= pd.to_datetime("{y}-{m}-{d}".format(y=timestep.year,m=end_date.month,d=end_date.day))):

            #Reset water entitlements every season
            #TODO: Update with values from policy module
            for WS in Manager.Farm.water_sources:
                if WS.name == 'Surface Water':
                    WS.allocation = 100
                else:
                    WS.allocation = 75
                #End if
            #End for

            Manager.season_started = True
            Manager.season_start_year = timestep.year

            #For debugging purposes
            season_counter += 1

            #For each field, set the crop to be planted
            # for Field in Manager.Farm.fields:
            #     Field.Crop = Manager.getNextCropInRotation(Field)
            # #End for

            #Run LP, determine water source for each timestep
            #Set num_field_combinations to 1 when testing single field at a time here
            #Otherwise if running for all fields at once, should be total number of possible combinations
            #combs = 1 #(len(Manager.Farm.fields) * 1 ) * len(Manager.Farm.water_sources)

            # print "BOTH FIELDS GET SET TO TOTAL FARM AREA, WHY!?"
            # print "BECAUSE THE RESULTS_OBS IS SET TO TOTAL FARM AREA INSTEAD OF FIELD AREA..."
            # print "RESULTS_OBS SHOULD HOLD IRRIGATION AREA.... WHY IS THIS NOT SET?"
            # print "Manager farm field areas"
            # for field in Manager.Farm.fields:
            #     print field.area
            
            #Generate all combinations
            field_combinations = Manager.generateFieldCombinations()
            c_log, b_ub_log, b_eq_log = Manager.LpInterface.genLogTemplates(field_combinations)

            for row in field_combinations.itertuples():

                # print "Field combination areas"
                # print row._1.area, row._2.area

                #Calculate results for the given combinations
                row = memoFieldCombinations(row, Manager.calcFieldCombination, Manager, c_log, b_ub_log, b_eq_log)
            #End for
            #memoFieldCombinations(field_combinations, Manager.calcFieldCombination, Manager, c_log, b_ub_log, b_eq_log, b_ub_memo={}, comp_memo={})

            A_ub = Manager.LpInterface.genAubs(c_log, Manager.Farm.water_sources)

            results_obs = Manager.LpInterface.runLP(results_obs, c_log, A_ub, b_ub_log, b_eq_log, field_combinations, Manager.Farm.water_sources)

            #For each season, if crop has gone past usual rotation length, determine next crop to cultivate given projected water allocation for growing season

        #End if

        assert season_counter <= 1, "MULTIPLE SEASONS WITHIN A SINGLE IRRIGATION YEAR"

        for Field in Manager.Farm.fields:

            #Plant crops for testing
            season_start, season_start_range = Field.Crop.getSeasonStartRange(timestep, step)

            if (Field.Crop.planted == False) and (current_ts >= pd.to_datetime(season_start)) and (current_ts <= pd.to_datetime(season_start_range)):

                #Update water entitlements for season
                Manager.Farm.water_sources = [ws.getCopy() for ws in Manager.water_sources]

                # Field.Crop = Manager.getNextCropInRotation(Field)

                if DEBUG:
                    print "::: Water Source Proportions: "
                #End if

                #field_area = results_obs.loc[0, 'farm_area']
                field_area = Field.area

                # if field_area == 140:
                #     print results_obs.head()
                #     import sys; sys.exit()

                if field_area == 0:
                    continue

                water_source_proportion = {}
                for WS in Manager.Farm.water_sources:
                    #field_area += results_obs.loc[0, 'farm_area']

                    temp_name = "{} {} {} {}".format(Field.name, Field.Storage.name, Field.Irrigation.name, Field.Crop.name)

                    water_source_proportion[WS.name] = results_obs.loc[0, temp_name+" "+WS.name] / field_area

                    if DEBUG:
                        print WS.name, water_source_proportion[WS.name]
                    #End if

                #End for

                summer_rainfall = Climate.getSummerRainfall(timestep, data=ClimateData)

                #Stored soil water at start of season is 25-30% of summer rainfall, as in Oliver et al. 2008; 2009
                Field.c_swd = -(summer_rainfall['rainfall'].sum() * 0.30)
                #Field.c_swd = min(-Field.Soil.TAW_mm + (summer_rainfall['rainfall'].sum() * 0.30), 0)

                Field.area = field_area

                Field.Crop.planted = True
                Field.season_ended = False
                Field.Crop.plant_date = current_ts

            #End if

            ###
            # TODO: Optimise which water source to get water from [DONE]
            #       Update all costs as years progress
            #           * Don't forget water costs, licence costs, etc.
            #       Check that pumping costs are done correctly [DONE, AS WELL AS I CAN]
            ###

            #If start of season, determine best crop
            #Or follow crop rotation

            if Field.Crop.planted == False:

                if DEBUG:
                    print "Crop not planted!"
                #End if

                #WARNING DIRECT COPY OF THE PROCESS BELOW
                try:
                    irrig_log = irrigation_log[Field.name]
                except:
                    irrigation_log[Field.name] = pd.DataFrame(columns=['Crop', 'ETo (mm)', 'Crop Coef (Kc)', 'Crop Water Use (ETc, mm)', 'Rainfall (mm)', \
                                                                       'Effective Rain (mm)', 'NID (mm)', 'SWD pre-Irrigation', 'Irrigation (mm)', 'C SWD (mm)', \
                                                                       'Field_water'])

                    irrigation_log[Field.name].index.name = 'Timestep'

                    irrig_log = irrigation_log[Field.name]
                #End try

                #temp_swd = Field.c_swd
                #reference crops use Field soil water
                irrig_log.loc[loop_timestep] = [
                    Field.Crop.name,
                    timestep_ETo,
                    None, #Crop Coef
                    None, #ETc
                    total_timestep_rainfall, 
                    0.0, #Effective Rainfall
                    None, #Net Irrigation Depth
                    None, #temp_swd
                    0.0, #Irrigation water
                    None,
                    0.0
                ]

                continue
            #End if

            e_rainfall_ML = Manager.calcEffectiveRainfallML(loop_timestep, timestep_rainfall, Field.area)
            ETc = (timestep_ETo * Field.Crop.getCurrentStageCropCoef(loop_timestep)) 
            water_deficit = (ETc - e_rainfall_ML) if (ETc - e_rainfall_ML) > 0 else 0.0
            nid = Field.calcNetIrrigationDepth(loop_timestep)

            temp_SWD = Field.c_swd

            if DEBUG:
                print "SWD before crop water use: ", Field.c_swd
                print "ETc: ", ETc
                print "Rain:", e_rainfall_ML
                print "WD: ", water_deficit

            flow_rate_Lps = Field.calcFlowRate()

            climate_params = {
                "ETc": ETc,
                "e_rainfall": e_rainfall_ML
            }

            RAW = Field.Soil.calcRAW(fraction=Field.Crop.getCurrentStageDepletionCoef(loop_timestep))

            soil_params = {
                "nid": nid,
                "RAW": RAW
            }

            irrig_water_to_apply_ML = Manager.calcIrrigationMLPerHa(Field, climate_params, soil_params, proportion=water_source_proportion) * Field.area

            #Ensure C_SWD doesn't go below what is possible
            #water_input_ML = irrig_water_to_apply_ML

            avg_ML_Ha = irrig_water_to_apply_ML / Field.area

            for WS in Manager.Farm.water_sources:
                #field_area += results_obs.loc[0, 'farm_area']

                temp_name = "{} {} {} {}".format(Field.name, Field.Storage.name, Field.Irrigation.name, Field.Crop.name)

                area = results_obs.loc[0, temp_name+" "+WS.name] 
                pumping_cost_Ha = WS.calcGrossPumpingCostsPerHa(flow_rate_Lps=flow_rate_Lps, est_irrigation_water_ML_per_Ha=avg_ML_Ha, additional_head=Field.Irrigation.head_pressure)
                timestep_pumping_cost += round(pumping_cost_Ha*area, 2)

            #End for

            #recharge = Field.updateCumulativeSWD(water_input_ML, 0.0)
            recharge = 0.0

            if DEBUG:
                print "Water Applied (ML): ", irrig_water_to_apply_ML
                print "SWD after irrigation: ", Field.c_swd
            #End if

            total_effective_rainfall[Field.name] = total_effective_rainfall[Field.name] + ((e_rainfall_ML / Field.area) * 100) \
                if Field.name in total_effective_rainfall.keys() else e_rainfall_ML
            total_water_applied[Field.name] = total_water_applied[Field.name] + irrig_water_to_apply_ML \
                if Field.name in total_water_applied.keys() else irrig_water_to_apply_ML
            
            Field.water_applied += irrig_water_to_apply_ML

            pumping_costs += timestep_pumping_cost

            #Save results into pandas df
            try:
                df = long_results[Field.name]
            except:
                long_results[Field.name] = pd.DataFrame(columns=['Field Name', 'Irrigation', 'Crop Name', 'SWD (mm)', 'SWD (Irrig+Rain) (mm)', 'Field Area (Ha)', 'Soil Type', \
                                                            'Max TAW (mm)', 'Current TAW (mm)', 'RAW (mm)', 'ETo (mm)', 'ETc (mm)', 'Crop Coef', \
                                                            'Rainfall (mm)', 'Effective Rainfall (mm)', \
                                                            'Irrigation (mm)', 'Surface Water', 'Groundwater', \
                                                            'Flow Rate (Lps)', 'Pumping Cost ($)', 'Net Irrigation Depth (mm)',\
                                                            'Gross Water Input (mm)', 'Recharge (mm)', 'P+I Crop Yield (t/Ha)', 'P Crop Yield (t/Ha)', \
                                                            'Total Profit ($/Ha)', 'Annualised Profit ($/Ha)', 'SSM (mm)', 'Seasonal Rainfall (mm)'])

                long_results[Field.name].index.name = 'Timestep'

                df = long_results[Field.name]
            #End try

            tmp = [
                Field.name,
                Field.Irrigation.name,
                Field.Crop.name,
                temp_SWD,
                Field.c_swd, 
                Field.area, 
                Field.Soil.name, 
                Field.Soil.TAW_mm, 
                Field.Soil.current_TAW_mm,
                Field.Soil.calcRAW(Field.Soil.current_TAW_mm, fraction=Field.Crop.depletion_fraction), 
                timestep_ETo,
                ETc, 
                Field.Crop.getCurrentStageCropCoef(loop_timestep),
                total_timestep_rainfall, 
                (e_rainfall_ML/Field.area)*100,
                avg_ML_Ha * 100,
                (avg_ML_Ha * 100) * water_source_proportion['Surface Water'],
                (avg_ML_Ha * 100) * water_source_proportion['Groundwater'],
                flow_rate_Lps, 
                timestep_pumping_cost, 
                -abs(Field.calcNetIrrigationDepth(loop_timestep)),
                (irrig_water_to_apply_ML/Field.area)*100, 
                (recharge*100),
                None,
                None,
                None,
                None,
                None,
                None
            ]

            df.loc[loop_timestep] = tmp

            try:
                irrig_log = irrigation_log[Field.name]
            except:
                irrigation_log[Field.name] = pd.DataFrame(columns=['Crop', 'ETo (mm)', 'Crop Coef (Kc)', 'Crop Water Use (ETc, mm)', 'Rainfall (mm)', \
                                                                   'Effective Rain (mm)', 'NID (mm)', 'SWD pre-Irrigation', 'Irrigation (mm)', 'C SWD (mm)', \
                                                                   'Field_water'])

                irrigation_log[Field.name].index.name = 'Timestep'
                irrig_log = irrigation_log[Field.name]
            #End try

            irrig_log.loc[loop_timestep] = [
                Field.Crop.name,
                timestep_ETo,
                Field.Crop.getCurrentStageCropCoef(loop_timestep),
                ETc,
                total_timestep_rainfall, 
                (e_rainfall_ML/Field.area)*100,
                -abs(Field.calcNetIrrigationDepth(loop_timestep)),
                temp_SWD,
                (irrig_water_to_apply_ML*100) / Field.area,
                Field.c_swd,
                Field.water_applied
            ]

            #Check if crop is ready for harvest (if applicable)
            if Field.Crop.harvest(loop_timestep) == True:

                if DEBUG:
                    print "Setting crop as not planted (harvested)"
                #End if

                Field.Crop.plant_date = None
                Field.Crop.planted = False
                Field.season_ended = True

                #Calculate and record estimated seasonal yield
                ssm = summer_rainfall['rainfall'].sum() * 0.30

                plant_available_water = Field.Soil.calcRAW(Field.Soil.current_TAW_mm, fraction=Field.Crop.depletion_fraction)

                # print str(loop_timestep)
                # print "Rainfall: ", total_effective_rainfall[Field.name]
                # print "Irrigation: ", ((Field.water_applied / Field.area) * 100)
                # print "summer rain: ", summer_rainfall['rainfall'].sum()
                # print "SSM:", ssm
                # print "----------------------"
                
                crop_yield = Manager.calcPotentialCropYield(ssm, (total_effective_rainfall[Field.name] + ((Field.water_applied / Field.area) * 100)), Field.Crop.et_coef, Field.Crop.wue_coef, plant_available_water)

                df.loc[loop_timestep, "P+I Crop Yield (t/Ha)"] = crop_yield

                crop_yield = Manager.calcPotentialCropYield(ssm, total_effective_rainfall[Field.name], Field.Crop.et_coef, Field.Crop.wue_coef, plant_available_water)
                df.loc[loop_timestep, "P Crop Yield (t/Ha)"] = crop_yield

                total_effective_rainfall[Field.name] = 0
                total_water_applied[Field.name] = 0
                Field.water_applied = 0

                df.loc[loop_timestep, "Total Profit ($/Ha)"] = crop_yield * Field.Crop.price_per_yield
                df.loc[loop_timestep, "Annualised Profit ($/Ha)"] = Manager.Finance.annualizeCapital(crop_yield * Field.Crop.price_per_yield, num_years=year_counter)

                df.loc[loop_timestep, "SSM (mm)"] = ssm

                season_start_end = Field.Crop.getSeasonStartEnd(loop_timestep)
                s = season_start_end[0]
                e = season_start_end[1]
                df.loc[loop_timestep, "Seasonal Rainfall (mm)"] = Climate.getSeasonalRainfall([s, e], data=ClimateData[['rainfall']])

            #End if

            if irrig_water_to_apply_ML > 0:

                if DEBUG:
                    print "Gross Water to Apply (ML): ", irrig_water_to_apply_ML
                    print "Area (Ha): ", Field.area
                    print "Total Rainfall (mm): ", total_timestep_rainfall
                #End if

                # if Field.Crop.plant_date != None:

                #     #Field.prev_ETc = ( ((irrig_water_to_apply_ML / Field.area) * 100) + total_timestep_rainfall) * Field.Irrigation.irrigation_efficiency
                #     scaling_coef = (Field.Irrigation.irrigation_efficiency / Manager.base_irrigation_efficiency)
                #     Field.prev_ETc = timestep_ETo * (Field.Crop.getCurrentStageDepletionCoef(loop_timestep) * scaling_coef)
                # else:
                #     Field.prev_ETc = 0.0

                # print "Prev ETc: ", Field.prev_ETc

        #End field loop

        #Check that all Fields have been harvested
        counter = 0
        if Manager.season_started and (current_ts > pd.to_datetime("{y}-{m}-{d}".format(y=Manager.season_start_year+1, m=end_date.month, d=end_date.day))):
            for Field in Manager.Farm.fields:
                if Field.season_ended:
                    counter += 1
            #End for

            #If all fields have been harvested
            if counter == len(Manager.Farm.fields):
                if DEBUG:
                    print "Season Ended!"
                #End if
                Manager.season_started = False

                #Debugging counter
                season_counter = 0

                year_counter += 1
            #End if
        #End if

        timestep = loop_timestep


    #End while

    # OUTPUT RESULTS ABOVE INTO CSV FOR VISUALIZATION
    for Field in Manager.Farm.fields:
        long_results[Field.name].loc['Total'] = long_results[Field.name].sum(axis=0, numeric_only=True)
        FileHandler.writeCSV(long_results[Field.name], 'output', '2nd_phase_{f}.csv'.format(f=Field.name))
        FileHandler.writeCSV(irrigation_log[Field.name], 'output', '2nd_phase_{f}_irrig_log.csv'.format(f=Field.name))
    #End for

    print "==== DONE ===="

