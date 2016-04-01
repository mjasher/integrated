from __future__ import division

from scipy.optimize import linprog as lp
from integrated.Modules.Climate.ClimateVariables import Climate

DEBUG = False

# from scipy.optimize import linprog as lp

# c = [-500, -400, -600, -350]
# A_ub = [[1, 1, 0, 0], [0, 0, 1, 1]]
# b_ub = [50, 45]
# bounds = ((0, 95), ) * 4

# x = lp(c=c, A_ub=A_ub, b_ub=b_ub, bounds=bounds)

# print x

def memoFieldCombinations(row, func, WaterSources, crop_rotations, lp_log, b_ub_log, b_eq_log, b_ub_memo={}, comp_memo={}):

    """
    Decorator method to allow memoization for generating Linear Programming coefficients and constraints

    """

    try:
        row_id = row.name
    except AttributeError:
        row_id = 0

    max_area = 0
    b_ub = []
    b_eq = []

    #For determining average water requirements
    water_req = []

    field_change = False
    for Field in row:
        if type(Field) is not FarmField:
            continue
        #End if

        implementation_change = False

        Store = Field.Storage
        Irrig = Field.Irrigation

        Field.Crop = Manager.getNextCropInRotation(Field)
        Field.Crop.planted = True

        # if (Field.Crop is None) or (Field.Crop.planted is False) or (hasattr(Field, 'Crop') == False):
        #     pass

        field_store = Field.name+" "+Store.name
        if field_store in comp_memo:
            storage_cost_per_Ha = comp_memo[field_store]
        else:
            #Calculate storage costs and memoize
            storage_cost = Store.calcStorageCosts(Store.storage_capacity_ML)
            storage_maintenance_cost = Store.calcMaintenanceCosts(Store.storage_capacity_ML)

            if Manager.getTotalFieldArea() == 0:
                storage_cost_per_Ha = (storage_cost + storage_maintenance_cost) * Store.storage_capacity_ML
            else:
                #WARNING: Storage Cost per Ha is calculated using Field Area, not actual used area
                storage_cost_per_Ha = (storage_cost+storage_maintenance_cost) / Manager.getTotalFieldArea()
            #End if

            # print "Storage Cost: ", storage_cost
            # print "Storage Maintenance: ", storage_maintenance_cost
            # print "Total Field Area: ", Manager.getTotalFieldArea()
            # print "Storage Cost: ", storage_cost_per_Ha

            assert np.isinf(storage_cost_per_Ha) == False, "Storage cost cannot be infinite"

            if Store.implemented is True:
                comp_memo[field_store] = storage_cost_per_Ha
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

        logs = [
            b_ub,
            b_eq,
            lp_log,            
            water_req
        ]

        field_change, max_area = func(row_id, Field, WaterSources, storage_cost_per_Ha, irrig_cost_per_Ha, max_area, logs, field_change)

        #If field has changed, enforce equality constraint
        # if field_change:
        #     b_eq.extend([max_area])

        Field.Crop.planted = False
        Field.Crop.plant_date = None

    #End field loop

    #Save results for this row
    b_ub_log.loc[row_id] = pd.Series(b_ub)
    b_eq_log.loc[row_id] = pd.Series(b_eq)

    if row_id not in b_ub_memo:
        b_ub_memo[row_id] = pd.Series(b_ub)
    #End if

    #Calculate total possible irrigation area
    total_water = sum([WS.entitlement for WS in Manager.Farm.water_sources])
    avg_water_req = sum(water_req)/len(water_req)
    possible_irrigation_area = total_water / avg_water_req

    b_ub.append(max_area) #min(max_area, possible_irrigation_area)

    try:
        total_area = sum([f.area if type(f) is FarmField else 0 for f in row])

        if field_change is False:
            lp_log.set_value(row_id, 'bounds', (0, min(possible_irrigation_area, total_area)))
        else:
            lp_log.set_value(row_id, 'bounds', (0, total_area) )

        lp_log.set_value(row_id, 'max_area', total_area)

    except ValueError as e:
        print lp_log
        import sys; sys.exit(e)
    #End try

    return row

#End memoFieldCombinations()

if __name__ == "__main__":

    from integrated.Modules.WaterSources.SurfaceWater import SurfaceWaterSource
    from integrated.Modules.WaterSources.Groundwater import GroundwaterSource

    import integrated.Modules.Farm.setup_dev as FarmConfig
    from integrated.Modules.Farm.Farms.FarmInfo import FarmInfo
    from integrated.Modules.Farm.Management.Manager import FarmManager
    from integrated.Modules.Farm.Management.LpInterface import LpInterface
    from integrated.Modules.Farm.Management.Finance import FarmFinance
    from integrated.Modules.Farm.WaterStorages.FarmDam import FarmDam
    from integrated.Modules.Farm.Fields.Field import FarmField
    from integrated.Modules.Farm.Fields.Soil import SoilType
    from integrated.Modules.Farm.Crops.CropInfo import CropInfo
    from integrated.Modules.Core.Handlers.FileHandler import FileHandler
    from integrated.Modules.Core.Handlers.BOMHandler import BOMHandler

    from scipy.optimize import linprog as lp

    import datetime
    import pandas as pd
    import numpy as np

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

        SurfaceWaterSource(name='Surface Water', water_level=0, entitlement=580.3, water_value_per_ML=150, cost_per_ML=24.86),
        GroundwaterSource(name='Groundwater', water_level=4, entitlement=75.0, water_value_per_ML=150, cost_per_ML=150)
        # WaterSources(name='Surface Water', water_level=2, entitlement=50.3, water_value_per_ML=150, cost_per_ML=75),
        # WaterSources(name='Groundwater', water_level=30, entitlement=24.0, water_value_per_ML=150, cost_per_ML=66)
    ]

    storages = [FarmDam(**FarmConfig.FarmDam_params.getParams())]
    #irrigations = [FarmConfig.PipeAndRiser.getCopy(), FarmConfig.Spray.getCopy(), FarmConfig.Flood.getCopy(), FarmConfig.Dryland.getCopy()]
    irrigations = [FarmConfig.Flood.getCopy(), FarmConfig.Dryland.getCopy()]

    #crops = [CropInfo(**cp.getParams()) for crop_name, cp in FarmConfig.crop_params.iteritems()]
    crops = [CropInfo(**FarmConfig.crop_params['Irrigated Wheat'].getParams())]

    FileHandler = FileHandler()
    LpInterface = LpInterface()
    Finance = FarmFinance()
    Manager = FarmManager(TestFarm, water_sources, storages, irrigations, crops, LpInterface, Finance)
    Manager.base_irrigation_efficiency = FarmConfig.Flood.irrigation_efficiency

    #Some useful data values may be found in the below
    #See Table 2, Echuca:
    #http://www.g-mwater.com.au/downloads/gmw/Groundwater/Lower_Campaspe_Valley_WSPA/30_Sept_2015-LOWER_CAMPASPE_VALLEY_WSPA_ANNUAL_REPORT_-_2014_15_-_SIGNED.pdf

    Manager.Farm.storages = {'Farm Dam': FarmDam(**FarmConfig.FarmDam_params.getParams())}

    FarmDam = FarmDam(**FarmConfig.FarmDam_params.getParams())

    fields = [
        FarmField(name='Field A', irrigation=FarmConfig.Flood.getCopy(), area=135, storage=FarmDam.getCopy(), soil=SoilType(**FarmConfig.Loam_params.getParams())),
        # FarmField(name='Field A', irrigation=FarmConfig.Flood.getCopy(), area=88, storage=FarmDam.getCopy(), soil=SoilType(**FarmConfig.Loam_params.getParams())),
        # FarmField(name='Field B', irrigation=FarmConfig.Spray.getCopy(), area=40, storage=FarmDam.getCopy(), soil=SoilType(**FarmConfig.Light_clay_params.getParams())),
        # FarmField(name='Field C', irrigation=FarmConfig.PipeAndRiser.getCopy(), area=10, storage=FarmDam.getCopy(), soil=SoilType(**FarmConfig.Clay_loam_params.getParams())),
        # FarmField(name='Field D', irrigation=FarmConfig.Spray.getCopy(), area=10, storage=FarmDam.getCopy(), soil=SoilType(**FarmConfig.Clay_loam_params.getParams()))
    ]

    Manager.Farm.fields = [field.getCopy() for field in fields]
    Manager.Farm.water_sources = [ws.getCopy() for ws in Manager.water_sources]

    #Generate all combinations
    all_combinations = Manager.generateFieldCombinations()

    field_combi = Manager.setupFieldComponentsStatus(all_combinations)

    del all_combinations
    field_combinations = Manager.generateCombinations(field_combi)    

    orig_field_combinations = field_combinations.copy()

    field_combinations['area_breakdown'] = 0

    A_ub = Manager.LpInterface.genAllAubs(len(Manager.Farm.fields), len(Manager.water_sources))

    years_ahead = 20
    field_results_memo = {}
    b_ub_memo = {}

    Manager.LpInterface.setLogTemplates(len(Manager.Farm.fields), len(Manager.water_sources), len(field_combinations))
    crop_rotations = Manager.crop_rotations

    #TODO:
    #  Implement assumed change of crops over years in response to climate/price/water
    #
    results = {}
    for n in xrange(years_ahead):

        lp_log = Manager.LpInterface.lp_log_template.copy()
        b_ub_log = Manager.LpInterface.b_ub_log_template.copy()
        b_eq_log = Manager.LpInterface.b_eq_log_template.copy()

        # Use of apply() causes the first row to be run twice; problematic when the irrigation system has not been implemented 
        # so use a traditional loop instead, even though it is slower
        for i, row in field_combinations.iterrows():
            #Calculate results for the given combinations
            row = memoFieldCombinations(row, Manager.calcFieldCombination, Manager.Farm.water_sources, crop_rotations, lp_log, b_ub_log, b_eq_log)
        #End for

        field_combinations = Manager.LpInterface.runLP(field_combinations, lp_log, A_ub, b_ub_log, b_eq_log, Manager.Farm.fields, Manager.Farm.water_sources)

        #Replace field objects with names
        results[n] = pd.DataFrame(columns=field_combinations.columns)
        results[n].index.name = 'Combination ID'
        for i in field_combinations.index:

            cols = field_combinations.columns
            for col_name in cols:

                obj = field_combinations.loc[i, col_name]

                if type(obj) is FarmField:
                    val = "{F} {S} {i} {c}".format(F=obj.name, S=obj.Storage.name, i=obj.Irrigation.name, c=obj.Crop.name) #, WS=obj.WaterSource.name
                else:
                    val = field_combinations.loc[i, col_name]
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
        print "  "+Field.Storage.name
        print "  "+Field.Irrigation.name
        Field.Crop.planted = False
        Field.Crop.plant_date = None
        Field.setIniSWD()

        print "  ", Field.Crop.planted
        print "  ", Field.Crop.plant_date
    #End for
    
    #Rerun using observed data

    start_date = datetime.date(year=1970, month=7, day=1)
    end_date = datetime.date(year=2009, month=6, day=30)
    timestep = datetime.date(year=1970, month=7, day=1)

    #TODO:
    #  Implement observed changes over years
    #  Manager.setupSeason() <- choose suitable crops
    #  Each timestep, LP the most suitable water source
    #    Generate the 'A_ub' and 'b_ub' once
    #    Generate 'c' each step if irrigations are implemented
    #    Remember, irrigations are not implemented until end of season...
    #
    step = 14 #days for each timestep
    step_ahead = datetime.timedelta(days=step)

    #TODO: RUN 2ND STEP FOR EACH FIELD COMBINATION
    """
    for field_combi in orig_field_combinations.itertuples():
        Manager.Farm.fields = list(field_combi)[1:]

        #While loop here

    """
    #Manager.Farm.fields = orig_field_combinations.iloc[best_field_config_index].tolist()


    results_obs = pd.DataFrame(lp_log[lp_log.index == 0].copy())

    pumping_costs = 0
    total_effective_rainfall = 0
    total_water_applied = 0

    long_results = {}
    irrigation_log = {}
    season_counter = 0
    while timestep < end_date:

        #End date of current timestep
        loop_timestep = timestep + step_ahead

        current_ts = pd.to_datetime(timestep)

        if DEBUG:
            #Show end date of timestep
            print "--- Start time step {s}-{e} ---\n".format(s=timestep, e=loop_timestep)
        #End if
        
        timestep_mask = (ClimateData.index >= str(timestep)) & (ClimateData.index < str(loop_timestep))

        #past_month = timestep - datetime.timedelta(month=1)
        #Get ETo for past month
        #past_month = "{y}-{m}-{d}".format(y=past_month.year, m=past_month.month-1, d=past_month.day)
        timestep_ETo = ClimateData.ET[timestep_mask].sum()

        #Sum of rainfall that occured in this timestep
        total_timestep_rainfall = ClimateData.rainfall[timestep_mask].sum()
        timestep_rainfall = ClimateData.rainfall[timestep_mask].copy()
        num_rainfall_events = (ClimateData.rainfall[timestep_mask] > 0).sum()

        total_field_area = 0
        timestep_pumping_cost = 0

        #TODO 
        #  LP to run once every timestep to determine areal proportion to be watered by each water source
        
        if (Manager.season_started == False) and (current_ts >= pd.to_datetime(str(timestep.year)+"-06-15")):

            #Reset water entitlements every season
            #TODO: Update with values from policy module
            for WS in Manager.Farm.water_sources:
                if WS.name == 'Surface Water':
                    WS.entitlement = 5000
                else:
                    WS.entitlement = 75
                #End if
            #End for

            lp_log, b_ub_log, b_eq_log = Manager.LpInterface.genLogTemplates(len(Manager.Farm.fields), len(Manager.Farm.water_sources), num_field_combinations=1) #1 because we're doing 1 field at a time here, should be set to number of fields
            memoFieldCombinations(Manager.Farm.fields, Manager.calcFieldCombination, Manager.Farm.water_sources, crop_rotations, lp_log, b_ub_log, b_eq_log, b_ub_memo={}, comp_memo={})
            results_obs = Manager.LpInterface.runLP(results_obs, lp_log, A_ub, b_ub_log, b_eq_log, Manager.Farm.fields, Manager.Farm.water_sources)
            Manager.season_started = True
            Manager.season_start_year = timestep.year

            #For debugging purposes
            season_counter += 1
        #End if

        assert season_counter <= 1, "MULTIPLE SEASONS WITHIN A SINGLE IRRIGATION YEAR"

        for Field in Manager.Farm.fields:

            #Plant crops for testing
            season_start, season_start_range = Field.Crop.getSeasonStartRange(timestep, step)

            if (Field.Crop.planted == False) and (current_ts >= pd.to_datetime(season_start)) and (current_ts <= pd.to_datetime(season_start_range)):

                #Update water entitlements for season
                Manager.Farm.water_sources = [ws.getCopy() for ws in Manager.water_sources]

                Field.Crop = Manager.getNextCropInRotation(Field)

                #LP Run used to be here

                field_area = 0
                for WS in Manager.Farm.water_sources:
                    field_area += results_obs.loc[0, Field.name+" "+WS.name+" Area"]
                #End for

                if DEBUG:
                    print "::: Water Source Proportions: "
                #End if
                water_source_proportion = {}
                for WS in Manager.Farm.water_sources:
                    water_source_proportion[WS.name] = results_obs.loc[0, Field.name+" "+WS.name+" Area"] / field_area

                    if DEBUG:
                        print WS.name, water_source_proportion[WS.name]
                    #End if

                #End for

                if DEBUG:
                    print "::: Setting stored soil water, 25-30 percent of summer rainfall as in Oliver et al."
                #End if

                season_data = Climate.getSummerRainfall(timestep, data=ClimateData)

                Field.c_swd = -(season_data['rainfall'].sum() * 0.3) #Field.setIniSWD()

                Field.area = field_area

                Field.Crop.planted = True
                Field.season_ended = False
                Field.Crop.plant_date = current_ts

            #End if

            ###
            # TODO: Optimise which water source to get water from [DONE]
            #       Update all costs as years progress
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

            #scaling_coef = (Field.Irrigation.irrigation_efficiency/Manager.base_irrigation_efficiency)
            #crop_water_use = (timestep_ETo * Field.Crop.getCurrentStageDepletionCoef(loop_timestep)) - Manager.calcEffectiveRainfallmm(timestep, total_timestep_rainfall)

            e_rainfall_ML = Manager.calcEffectiveRainfallML(loop_timestep, timestep_rainfall, Field.area)
            #e_rainfall_ML = Manager.calcEffectiveRainfallML(loop_timestep, num_rainfall_events, total_timestep_rainfall, Field.area)
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

            #gross_water_to_apply_ML = ((water_deficit * Field.Irrigation.irrigation_efficiency) / 100) * Field.area
            gross_water_to_apply_ML = Manager.calcGrossIrrigationMLPerHa(Field, climate_params, soil_params, proportion=water_source_proportion) * Field.area

            #Ensure C_SWD doesn't go below what is possible
            
            water_input_ML = gross_water_to_apply_ML

            avg_ML_Ha = gross_water_to_apply_ML / Field.area

            for WS in Manager.Farm.water_sources:
                
                area = results_obs.loc[0, Field.name+" "+WS.name+" Area"]

                pumping_cost_Ha = WS.calcGrossPumpingCostsPerHa(flow_rate_Lps=flow_rate_Lps, est_irrigation_water_ML_per_Ha=avg_ML_Ha, additional_head=Field.Irrigation.head_pressure)

                timestep_pumping_cost += round(pumping_cost_Ha*area, 2)
            #End for

            #recharge = Field.updateCumulativeSWD(water_input_ML, 0.0)
            recharge = 0.0

            if DEBUG:
                print "Water Applied (ML): ", gross_water_to_apply_ML
                print "SWD after irrigation: ", Field.c_swd
            #End if

            total_effective_rainfall += total_timestep_rainfall
            total_water_applied += water_input_ML
            Field.water_applied += gross_water_to_apply_ML

            pumping_costs += timestep_pumping_cost

            #Save results into pandas df
            try:
                df = long_results[Field.name]
            except:
                long_results[Field.name] = pd.DataFrame(columns=['Field Name', 'Crop Name', 'SWD (mm)', 'SWD (Irrig+Rain) (mm)', 'Field Area (Ha)', 'Soil Type', \
                                                            'Max TAW (mm)', 'Current TAW (mm)', 'RAW (mm)', 'ETo (mm)', 'ETc (mm)', 'Crop Coef', \
                                                            'Rainfall (mm)', 'Effective Rainfall (mm)', \
                                                            'Irrigation (mm)', 'Flow Rate (Lps)', 'Pumping Cost ($)', 'Net Irrigation Depth (mm)',\
                                                            'Gross Water Input (mm)', 'Recharge (mm)'])

                long_results[Field.name].index.name = 'Timestep'

                df = long_results[Field.name]
            #End try

            tmp = [
                Field.name,
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
                flow_rate_Lps, 
                timestep_pumping_cost, 
                -abs(Field.calcNetIrrigationDepth(loop_timestep)),
                (water_input_ML/Field.area)*100, 
                (recharge*100)
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
                (gross_water_to_apply_ML*100) / Field.area,
                Field.c_swd,
                Field.water_applied
            ]

            # print "WATER TO APPLY AND HALF OF THAT 2"
            # print gross_water_to_apply_ML
            # print gross_water_to_apply_ML * 0.5
            # print Field.area
            # print Field.Crop.planted
            # print "---------------------"

            #Check if crop is ready for harvest (if applicable)
            if Field.Crop.harvest(loop_timestep) == True:

                if DEBUG:
                    print "Setting crop as not planted (harvested)"
                Field.Crop.plant_date = None
                Field.Crop.planted = False
                Field.season_ended = True
            #End if

            if gross_water_to_apply_ML > 0:

                if DEBUG:
                    print "Gross Water to Apply (ML): ", gross_water_to_apply_ML
                    print "Area (Ha): ", Field.area
                    print "Total Rainfall (mm): ", total_timestep_rainfall
                #End if

                # if Field.Crop.plant_date != None:

                #     #Field.prev_ETc = ( ((gross_water_to_apply_ML / Field.area) * 100) + total_timestep_rainfall) * Field.Irrigation.irrigation_efficiency
                #     scaling_coef = (Field.Irrigation.irrigation_efficiency / Manager.base_irrigation_efficiency)
                #     Field.prev_ETc = timestep_ETo * (Field.Crop.getCurrentStageDepletionCoef(loop_timestep) * scaling_coef)
                # else:
                #     Field.prev_ETc = 0.0

                # print "Prev ETc: ", Field.prev_ETc

        #End field loop

        #Check that all Fields have been harvested
        counter = 0
        if Manager.season_started and (current_ts > pd.to_datetime(str(Manager.season_start_year+1)+"-{m}-{d}".format(m=5, d=15))):
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
                season_counter = 0
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

    import sys
    sys.exit()


