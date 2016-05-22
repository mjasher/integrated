from __future__ import division

from integrated.Modules.Core.Handlers.FileHandler import FileHandler

from integrated.Modules.Farm import setup_dev as FarmConfig
from integrated.Modules.Farm.WaterSources.SurfaceWater import SurfaceWaterSource
from integrated.Modules.Farm.WaterSources.Groundwater import GroundwaterSource
from integrated.Modules.Farm.Farms.FarmInfo import FarmInfo
from integrated.Modules.Farm.Management.Manager import FarmManager
from integrated.Modules.Farm.Management.Finance import FarmFinance
from integrated.Modules.Farm.Fields.Field import FarmField
from integrated.Modules.Farm.Fields.Soil import SoilType
from integrated.Modules.Farm.Crops.CropInfo import CropInfo

from scipy.optimize import linprog as lp
import datetime
import pandas as pd
import numpy as np

DEBUG = False

def memoFieldCombinations(row, func, Manager, c_log, b_ub_log, b_eq_log, b_ub_memo={}, comp_memo={}, water_applied=None):

    """
    Decorator method to allow memoization for generating Linear Programming coefficients and constraints

    TODO: No need to generate b_ub here, this is now handled in the LPInterface

    :param row: Tuple representing a Pandas Dataframe row generated using pd.itertuples() which represents a farm-field combination
    :param func: The function to run for the given field combination, typically Manager.calcFieldCombination()
    :param Manager: Farm Manager object
    :param c_log: Pandas dataframe used to store the Scipy Linear Programming :math:`c` values for the given row
    :param b_ub_log: Pandas dataframe used to store the Scipy Linear Programming right hand upper bound values
    :param b_eq_log: Pandas dataframe used to store the Scipy Linear Programming right hand equality values
    :param b_ub_memo: Dict used to store previously generated right hand upper bound values 
    :param comp_memo: Dict used to store previously generated :math:`c` values for field components
    :param water_applied: Dict for each field with amount of water (in ML) already applied

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

        #Keep a copy to reset later
        crop_planted = Field.Crop.planted
        crop_plant_date = Field.Crop.plant_date if hasattr(Field.Crop, 'plant_date') else None
        Field.Crop.planted = True

        field_store = Field.name+" "+Store.name

        #storage_cost_per_Ha = comp_memo.get(field_store, Manager.calcStorageCostsPerHa(Field))
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

        field_change = func(row_id, Field, WaterSources, storage_cost_per_Ha, irrig_cost_per_Ha, logs, field_change, water_applied)

        Field.Crop.planted = crop_planted
        Field.Crop.plant_date = crop_plant_date

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
    from integrated.Modules.Policy.WaterPolicy import SurfaceWaterPolicy
    from integrated.Modules.Farm.WaterStorages.FarmDam import FarmDam
    from integrated.Modules.Farm.Management.LpInterface import LpInterface

    #Tired of having columns split over several lines
    pd.set_option('max_colwidth', 5000)
    pd.set_option('display.width', 5000)

    TestFarm = FarmInfo(**FarmConfig.BASE_FARM.getParams())
    test_farm_area = 100 #100 Ha

    print "Processing {farm_name}".format(farm_name=TestFarm.name)
    print "--------------------------"

    print "Setting up historical data for Echuca area"
    print "--------------------------"

    #Real data for Echuca
    ClimateData = FileHandler().loadCSV('test_data/climate/climate.csv', columns=['Date', '406265_rain', '406265_evap'], index_col=0, dayfirst=True, parse_dates=True)
    ClimateData.index.name = 'Date'
    ClimateData.columns = ['rainfall', 'ET']

    Climate = Climate(data=ClimateData, low_rainfall_thres_mm=400, high_rainfall_thres_mm=500)
    SurfacePolicy = SurfaceWaterPolicy(Climate)

    #Determine water source costs
    #TODO: Separate this out!
    sw_yearly = FarmConfig.sw_costs['Campaspe']['yearly_costs']
    sw_seasonal = FarmConfig.sw_costs['Campaspe']['water_costs']

    sw_yearly_costs = sw_yearly.loc[['service', 'service_point', 'service_point_local_read', 'surface_drainage_service'], :].sum()['Amount ($/Point)']

    #12ML/Day irrigation system capacity, price simulator says to divide entitlement with 100 = 4.35
    sw_yearly_costs += sw_yearly.loc[['infrastructure_access (ML/Day)'], :].sum()['Amount ($/Point)'] * 0 #4.35 
    sw_yearly_costs += sw_yearly.loc[['area_fee ($/Ha)'], :].sum()['Amount ($/Point)'] * test_farm_area

    sw_seasonal_costs = sw_seasonal.loc[['access_fee', 'resource_management_fee', 'high_reliability', 'high_reliability_storage'], :].sum()['Amount ($/ML)']
    sw_overuse_costs = sw_seasonal.loc[['above_entitlement_storage', 'overuse_fee'], :]

    gw_yearly = FarmConfig.gw_costs['Campaspe']['yearly_costs']
    gw_seasonal = FarmConfig.gw_costs['Campaspe']['water_costs']

    #Not considering Bore implementation costs (assuming already constructed)
    #gw_implementation_costs = gw_costs['Campaspe']['bore_costs'].loc[['licence_application', 'bore_construction_licence']]

    gw_yearly_costs = gw_yearly.loc[['service', 'service_point', 'access_service_point'], :].sum()['Amount ($/Bore)']
    gw_seasonal_costs = gw_seasonal.loc[['access', 'resource_management'], :].sum()['Amount ($/ML)']
    gw_overuse_costs = sw_seasonal.loc[['overuse_fee'], :]

    water_sources = [
        #See information_source in WaterSource/data directory
        SurfaceWaterSource(name='Surface Water', water_level=0, entitlement=30.0, perc_allocation=1, trade_value_per_ML=150, cost_per_ML=sw_seasonal_costs, yearly_costs=sw_yearly_costs, Pump=FarmConfig.NoPump.getCopy() ), #FarmConfig.DieselPump.getCopy()), #24.86+10.57
        GroundwaterSource(name='Groundwater', water_level=4, entitlement=246.0, perc_allocation=1, trade_value_per_ML=150, cost_per_ML=gw_seasonal_costs, yearly_costs=gw_yearly_costs+138, Pump=FarmConfig.DieselPump.getCopy()) #138 yearly licence renewal cost based on 30 years
    ]

    storages = [FarmDam(**FarmConfig.FarmDam_params.getParams())]

    #irrigations = [FarmConfig.Flood.getCopy(), FarmConfig.Spray.getCopy(), FarmConfig.Drip.getCopy()] 
    irrigations = [FarmConfig.Gravity.getCopy(), FarmConfig.Flood.getCopy(), FarmConfig.Spray.getCopy(), FarmConfig.Drip.getCopy()]

    #crops = [CropInfo(**cp.getParams()) for crop_name, cp in FarmConfig.crop_params.iteritems()]
    # crops = [CropInfo(**FarmConfig.crop_params['Irrigated Winter Wheat'].getParams()), \
    #          CropInfo(**FarmConfig.crop_params['Dryland Winter Wheat'].getParams()), \
    #          CropInfo(**FarmConfig.crop_params['Irrigated Winter Barley'].getParams()),]

    # crops = [CropInfo(**FarmConfig.crop_params['Irrigated Winter Canola'].getParams()), \
    #          CropInfo(**FarmConfig.crop_params['Dryland Winter Canola'].getParams())]

    #irrig_crops = [CropInfo(**FarmConfig.crop_params['Irrigated Processing Tomato'].getParams())]
    irrig_crops = [CropInfo(**FarmConfig.crop_params['Irrigated Winter Barley'].getParams()), \
              CropInfo(**FarmConfig.crop_params['Irrigated Winter Wheat'].getParams()), \
              CropInfo(**FarmConfig.crop_params['Irrigated Winter Canola'].getParams())]

    dryland_crops = [CropInfo(**FarmConfig.crop_params['Dryland Winter Barley'].getParams()), \
              CropInfo(**FarmConfig.crop_params['Dryland Winter Wheat'].getParams()), \
              CropInfo(**FarmConfig.crop_params['Dryland Winter Canola'].getParams())]

    crops = irrig_crops + dryland_crops

    FileHandler = FileHandler()
    LpInterface = LpInterface()
    Finance = FarmFinance()
    Manager = FarmManager(TestFarm, water_sources, storages, irrigations, crops, LpInterface, Finance)
    Manager.base_irrigation_efficiency = FarmConfig.Gravity.getCopy().irrigation_efficiency

    Manager.crop_rotations = {
        'irrigated': irrig_crops[:],
        'dryland': dryland_crops[:]
    }

    #Some useful data values may be found in the below
    #See Table 2, Echuca:
    #http://www.g-mwater.com.au/downloads/gmw/Groundwater/Lower_Campaspe_Valley_WSPA/30_Sept_2015-LOWER_CAMPASPE_VALLEY_WSPA_ANNUAL_REPORT_-_2014_15_-_SIGNED.pdf

    Manager.Farm.storages = {'Farm Dam': FarmDam(**FarmConfig.FarmDam_params.getParams())}

    FarmDam = FarmDam(**FarmConfig.FarmDam_params.getParams())

    fields = [
        FarmField(name='Field A', irrigation=FarmConfig.Gravity.getCopy(), area=100, storage=FarmDam.getCopy(), soil=SoilType(**FarmConfig.Loam_params.getParams())),
        #FarmField(name='Field B', irrigation=FarmConfig.Drip.getCopy(), area=40, storage=FarmDam.getCopy(), soil=SoilType(**FarmConfig.Light_clay_params.getParams())),
        # FarmField(name='Field C', irrigation=FarmConfig.PipeAndRiser.getCopy(), area=10, storage=FarmDam.getCopy(), soil=SoilType(**FarmConfig.Clay_loam_params.getParams())),
        # FarmField(name='Field D', irrigation=FarmConfig.Spray.getCopy(), area=10, storage=FarmDam.getCopy(), soil=SoilType(**FarmConfig.Clay_loam_params.getParams()))
    ]

    Manager.Farm.fields = [field.getCopy() for field in fields]
    Manager.Farm.water_sources = [ws.getCopy() for ws in Manager.water_sources]

    #Generate all combinations
    field_combinations = Manager.generateFieldCombinations()
    orig_field_combinations = field_combinations.copy()

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
                    val = "{F} {S} {i}".format(F=obj.name, S=obj.Storage.name, i=obj.Irrigation.name) #, WS=obj.WaterSource.name
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

    #print results[n]

    #Get best performing configuration
    best_field_config_index = results[n]['total_profit'].idxmax()

    Manager.Farm.fields = [f.getCopy() for f in orig_field_combinations.iloc[best_field_config_index].tolist()[:]]

    print "Best Field Setup: "
    for Field in Manager.Farm.fields:
        print Field.name
        print "  Storage: "+Field.Storage.name
        print "  Irrigation: "+Field.Irrigation.name
        Field.Crop.planted = False
        Field.Crop.plant_date = None
        Field.setIniSWD()

        #If not Gravity, should not be implemented and incurr construction costs
        #TODO: Better way to implement this check
        if (Field.Irrigation.name != 'Gravity') or (Field.Irrigation.name != 'Dryland'):
            Field.Irrigation.implemented = False

        print "  Planted? ", Field.Crop.planted
        print "  Plant Date: ", Field.Crop.plant_date
    #End for
    
    #Rerun using observed data

    start_date = datetime.date(year=1950, month=5, day=1)
    end_date = datetime.date(year=1988, month=4, day=30)
    timestep = datetime.date(year=1950, month=5, day=1)

    #TODO:
    #  START INCORPORATING CHANGES OVER YEARS (CLIMATE, ALLOCATIONS, ETC.)
    #  Implement observed changes over years
    #  
    #  Each timestep, LP the most suitable water source
    #    Generate 'c' each step if irrigations are implemented [DONE]
    #    Generate b and A upper bounds each step (due to changing conditions) [DONE]
    #    Remember, irrigations are not implemented until end of season...
    ############
    
    step = 7 #days for each timestep
    step_ahead = datetime.timedelta(days=step)

    #TODO: RUN 2ND STEP FOR EACH FIELD COMBINATION
    """
    for field_combi in orig_field_combinations.itertuples():
        Manager.Farm.fields = list(field_combi)[1:]

        #While loop here

    """
    results_obs = None

    pumping_costs = {}
    total_effective_rainfall = {}
    total_water_applied = {}

    long_results = {}
    irrigation_log = {}
    season_counter = 0 #debugging counter

    year_counter = 1 #Count number of years to annualise profits
    debug_counter = 1 #for displaying of messages after a certain number of iterations

    #TODO: Move these to config file
    gw_alloc_avg_years = 3 #Number of years to average GW allocations over, see Lower Campaspe Valley WSPA GW Management Plan Nov 2013 (p 13)
    max_gw_over_alloc = 0.3 #Max overallocation of GW allowed
    good_sw_condition = 0.9 #What is considered good SW allocation
    past_gw_allocs = [] #records past GW allocations for allocation adjustment

    print "---- Starting long loop ----"
    while timestep < end_date:

        #End date of current timestep
        loop_timestep = timestep + pd.Timedelta(step_ahead, unit='d')

        current_ts = pd.to_datetime(str(timestep)) #pd.Timestamp.date(pd.to_datetime(str(timestep)))

        if DEBUG:
            #Show end date of timestep
            print "--- Start time step {s}-{e} ---\n".format(s=timestep, e=loop_timestep)
        #End if

        #Get relevant subset of climate data
        timestep_mask = (ClimateData.index >= str(timestep)) & (ClimateData.index < str(loop_timestep))

        #Get ETo for past month
        timestep_ETo = ClimateData.ET[timestep_mask].sum()

        #Sum of rainfall that occured in this timestep
        total_timestep_rainfall = ClimateData.rainfall[timestep_mask].sum()
        timestep_rainfall = ClimateData.rainfall[timestep_mask].copy()
        num_rainfall_events = (ClimateData.rainfall[timestep_mask] > 0).sum()

        total_field_area = 0
        timestep_pumping_cost = 0
        season_end_date = pd.to_datetime("{y}-{m}-{d}".format(y=timestep.year,m=end_date.month,d=end_date.day))
        if (Manager.season_started == False) and (current_ts >= season_end_date):

            #Reset field details (specifically area)
            #Manager.Farm.fields = [f.getCopy() for f in orig_field_combinations.iloc[best_field_config_index].tolist()[:]]
            temp_fields = [f.getCopy() for f in orig_field_combinations.iloc[best_field_config_index].tolist()[:]]

            #Reset field area
            for f in Manager.Farm.fields:
                orig_area = temp_fields[[index for index, t_f in enumerate(temp_fields) if t_f.name == f.name][0]].area
                f.area = orig_area
            #End for
            del temp_fields

            #Determine this year's SW allocation based on previous year's rainfall
            for WS in Manager.Farm.water_sources:
                if WS.name == 'Surface Water':
                    WS.perc_allocation = SurfacePolicy.determineAnnualAllocation(Climate.getAnnualRainfall(timestep.year-1))
                    #WS.entitlement = 400
                #End if
                WS.updateAllocation()
            #End for

            #TODO: Move below into GW Policy
            #Allow overallocation of GW under poor SW conditions, under allocate when SW conditions are good or every n years, where n=5
            #This is equivalent to Option 4 in Maules Creek model
            SW_ws = [ws for ws in Manager.Farm.water_sources if ws.name == 'Surface Water'][0]
            GW_ws = [ws for ws in Manager.Farm.water_sources if ws.name != 'Surface Water'][0]
            if len(past_gw_allocs) < (gw_alloc_avg_years-1):
                #if allocation is above good SW index
                if SW_ws.perc_allocation >= 0.9:
                    #correct gw allocation to maintain average
                    GW_ws.perc_allocation = max(0, (len(past_gw_allocs)+1) - sum(past_gw_allocs))
                    past_gw_allocs = []
                else:
                    #Overallocate GW
                    sw_deficit = SurfacePolicy.calcDeficit(SW_ws.perc_allocation, SW_ws.entitlement) #Calculate SW deficit
                    GW_ws.perc_allocation = 1.0 + min(max_gw_over_alloc, sw_deficit / GW_ws.entitlement)
                    past_gw_allocs.append(GW_ws.perc_allocation)
                #End if
            else:
                #Forced reduction of GW allocations to maintain n year average
                GW_ws.perc_allocation = max(0, gw_alloc_avg_years - sum(past_gw_allocs))
                past_gw_allocs = []
            #End if

            Manager.season_started = True
            Manager.season_start_year = timestep.year

            #For debugging purposes
            season_counter += 1
            
            #Generate all combinations
            field_combinations = Manager.generateFieldCombinations()

            c_log, b_ub_log, b_eq_log = Manager.LpInterface.genLogTemplates(field_combinations)

            for row in field_combinations.itertuples():
                #Calculate results for the given combinations
                row = memoFieldCombinations(row, Manager.calcFieldCombination, Manager, c_log, b_ub_log, b_eq_log)
            #End for

            A_ub = Manager.LpInterface.genAubs(c_log, Manager.Farm.water_sources)

            results_obs = Manager.LpInterface.runLP(results_obs, c_log, A_ub, b_ub_log, b_eq_log, field_combinations, Manager.Farm.water_sources)

            #Get area of optimum configuration
            area_breakdown = results_obs.loc[results_obs['profit'].argmin(), 'area_breakdown'].split('| ')
            area_breakdown = [float(i) for i in area_breakdown]

            #Associate field with area, and calculate total area possible from both water sources
            temp_df = pd.DataFrame({'fields': Manager.LpInterface.A_ub_map, 'area': area_breakdown})
            temp_df['field_name'] = [df_f.name for df_f in temp_df['fields']]
            #temp_df['area'] = temp_df[temp_df['field_name'] == f.name].loc[:, 'area'].sum()

            temp_df = temp_df.groupby(['fields']).sum()

            temp_df['field_name'] = [df_f.name for df_f in temp_df.index]

            #Update field areas and cultivated crop to those determined as the most optimal
            for f in Manager.Farm.fields:

                f.area = temp_df.loc[temp_df['field_name'] == f.name, 'area'].sum()

                if len(temp_df[temp_df['area'] > 0]) > 0:
                    f.Crop = temp_df[temp_df['area'] > 0].index[0].Crop
                else:
                    #Not economical to grow anything
                    f.Crop = temp_df.index[0].Crop
                #End if
            #End for

        elif Manager.season_started == True:

            #Run LP to update areal proportion to be watered from each water source

            #c_log, b_ub_log, b_eq_log = Manager.LpInterface.genLogTemplates(field_combinations)
            for row in field_combinations.itertuples():

                #Calculate results for the given combinations
                row = memoFieldCombinations(row, Manager.calcFieldCombination, Manager, c_log, b_ub_log, b_eq_log, total_water_applied)
            #End for

            A_ub = Manager.LpInterface.genAubs(c_log, Manager.Farm.water_sources)

            results_obs = Manager.LpInterface.runLP(results_obs, c_log, A_ub, b_ub_log, b_eq_log, field_combinations, Manager.Farm.water_sources)

        else:
            #Not in irrigation season and growing season has not started
            timestep = loop_timestep
            continue
        #End if

        assert season_counter <= 1, "MULTIPLE SEASONS WITHIN A SINGLE IRRIGATION YEAR"

        for Field in Manager.Farm.fields:

            season_start, season_start_range = Field.Crop.getSeasonStartRange(timestep, step)

            if (Field.Crop.planted == False) and (current_ts >= pd.to_datetime(season_start)) and (current_ts <= pd.to_datetime(season_start_range)):

                #Update water allocation for season
                Manager.Farm.water_sources = [ws.getCopy() for ws in Manager.water_sources]

                field_area = Field.area

                if field_area == 0:
                    continue
                #End if

                #Get proportion of GW and SW to use this season
                water_source_proportion = {}
                for WS in Manager.Farm.water_sources:

                    temp_name = "{F} {S} {I}".format(F=Field.name, S=Field.Storage.name, I=Field.Irrigation.name)
                    water_source_proportion[WS.name] = results_obs.loc[results_obs['profit'].argmin(), temp_name+" "+WS.name] / field_area

                #End for

                summer_rainfall = Climate.getSummerRainfall(timestep, data=ClimateData)

                #Stored soil water at start of season is 25-30% of summer rainfall, as in Oliver et al. 2008; 2009
                Field.c_swd = -(summer_rainfall['rainfall'].sum() * 0.30)
                #Field.c_swd = min(-Field.Soil.TAW_mm + (summer_rainfall['rainfall'].sum() * 0.30), 0)

                assert Field.Crop.plant_date == None, "Plant date should not be set yet..."

                Field.Crop.planted = True
                Field.season_ended = False
                Field.Crop.plant_date = current_ts

                crop_planted_debug = True

            #End if

            ###
            # TODO: Optimise which water source to get water from [DONE]
            #       Update all costs as years progress
            #           * Don't forget water costs, licence costs, etc.
            #       Check that pumping costs are done correctly [DONE, AS WELL AS I CAN]
            ###

            if Field.Crop.planted == False:

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
                irrig_log.loc[loop_timestep] = [ Field.Crop.name, timestep_ETo, \
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

                #No crop planted in this field, so move on to the next field
                continue
            #End if

            #If start of season, determine best crop
            #Or follow crop rotation

            #Crop has been planted for this field, calculate Irrigation water to apply

            e_rainfall_ML = Manager.calcEffectiveRainfallML(loop_timestep, timestep_rainfall, Field.area)
            ETc = (timestep_ETo * Field.Crop.getCurrentStageCropCoef(loop_timestep)) 
            water_deficit = (ETc - e_rainfall_ML) if (ETc - e_rainfall_ML) > 0 else 0.0
            nid = Field.calcNetIrrigationDepth(loop_timestep)

            temp_SWD = Field.c_swd
            flow_rate_Lps = Field.calcFlowRate()
            climate_params = {"ETc": ETc, "e_rainfall": e_rainfall_ML}
            RAW = Field.Soil.calcRAW(fraction=Field.Crop.getCurrentStageDepletionCoef(loop_timestep))

            soil_params = {"nid": nid, "RAW": RAW}

            #This also updates CSWD (I know this is bad. I will fix it up afterwards, just need it working for now)
            irrig_water_to_apply_ML = Manager.calcIrrigationMLPerHa(Field, climate_params, soil_params) * Field.area

            #Do not irrigate if outside the irrigation season (August to May in the Campaspe)
            if Climate.inIrrigationSeason(loop_timestep, months=[8, 5], days=[15, 15], data=ClimateData) == False:
                irrig_water_to_apply_ML = 0
            #End if

            #Cannot irrigate if irrigation system is not in place
            if Field.Irrigation.implemented == False:
                irrig_water_to_apply_ML = 0
            #End if

            #Update water allocation volume
            Manager.updateWaterAllocations(irrig_water_to_apply_ML, water_source_proportion)

            #Ensure C_SWD doesn't go below what is possible
            avg_ML_Ha = irrig_water_to_apply_ML / Field.area

            pumping_costs[Field.name] = pumping_costs.get(Field.name, 0)
            field_pump_costs = pumping_costs[Field.name]

            #Calc pumping costs for this timestep
            for WS in Manager.Farm.water_sources:

                temp_name = "{F} {S} {I}".format(F=Field.name, S=Field.Storage.name, I=Field.Irrigation.name)

                ws_area = results_obs.loc[results_obs['profit'].argmin(), temp_name+" "+WS.name]
                pumping_cost_Ha = WS.calcGrossPumpingCostsPerHa(flow_rate_Lps=flow_rate_Lps, est_irrigation_water_ML_per_Ha=avg_ML_Ha, additional_head=Field.Irrigation.head_pressure)
                timestep_pumping_cost += round(pumping_cost_Ha*ws_area, 2)
                field_pump_costs += round(pumping_cost_Ha*ws_area, 2)

            #End for

            pumping_costs[Field.name] = field_pump_costs

            #TODO: Pass estimated recharge values to groundwater-surface water model?
            #recharge = Field.updateCumulativeSWD(water_input_ML, 0.0)
            recharge = 0.0

            #Log amount of effective rainfall
            total_effective_rainfall[Field.name] = total_effective_rainfall[Field.name] + ((e_rainfall_ML / Field.area) * 100) \
                if Field.name in total_effective_rainfall.keys() else e_rainfall_ML

            #Irrigation water applied is modified to account for inefficiencies 
            #otherwise less efficient irrigations apply more water, which results in higher yields
            #In essense we are saying "how much water was used effectively?"
            total_water_applied[Field.name] = total_water_applied[Field.name] + (irrig_water_to_apply_ML * Field.Irrigation.irrigation_efficiency) \
                if Field.name in total_water_applied.keys() else (irrig_water_to_apply_ML * Field.Irrigation.irrigation_efficiency)
            
            Field.water_applied += (irrig_water_to_apply_ML * Field.Irrigation.irrigation_efficiency)
            

            #Save results into Pandas Dataframe. temp_results is a reference to the dataframe so I don't have to keep typing it out
            try:
                temp_results = long_results[Field.name]
            except KeyError as e:
                long_results[Field.name] = pd.DataFrame(columns=['Field Name', 'Irrigation', 'Crop Name', 'SWD (mm)', 'SWD (Irrig+Rain) (mm)', 'Field Area (Ha)', 'Soil Type', \
                                                            'Max TAW (mm)', 'Current TAW (mm)', 'RAW (mm)', 'ETo (mm)', 'ETc (mm)', 'Crop Coef', \
                                                            'Rainfall (mm)', 'Effective Rainfall (mm)', \
                                                            'Irrigation (mm)', 'Surface Water (mm)', 'Groundwater (mm)', \
                                                            'Flow Rate (Lps)', 'Pumping Cost ($)', 'Net Irrigation Depth (mm)',\
                                                            'Gross Water Input (mm)', 'Recharge (mm)', 'P+I Crop Yield (t/Ha)', 'P Crop Yield (t/Ha)', \
                                                            'Total Field Profit ($/Ha)', 'Annualised Field Profit ($/Ha)', 'SSM (mm)', 'Seasonal Rainfall (mm)'])

                long_results[Field.name].index.name = 'Timestep'

                temp_results = long_results[Field.name]
            #End try

            assert len(long_results) != 0, "Result DF cannot be empty!"

            tmp = [
                Field.name, Field.Irrigation.name, \
                Field.Crop.name, temp_SWD, \
                Field.c_swd, Field.area, \
                Field.Soil.name, Field.Soil.TAW_mm, \
                Field.Soil.current_TAW_mm, Field.Soil.calcRAW(Field.Soil.current_TAW_mm, fraction=Field.Crop.depletion_fraction), \
                timestep_ETo, ETc, \
                Field.Crop.getCurrentStageCropCoef(loop_timestep), total_timestep_rainfall, \
                (e_rainfall_ML/Field.area)*100, avg_ML_Ha * 100, \
                (avg_ML_Ha * 100) * water_source_proportion['Surface Water'],
                (avg_ML_Ha * 100) * water_source_proportion['Groundwater'],
                flow_rate_Lps, field_pump_costs, \
                -abs(Field.calcNetIrrigationDepth(loop_timestep)), (irrig_water_to_apply_ML/Field.area)*100, \
                (recharge*100),
                None,
                None,
                None,
                None,
                None,
                None
            ]

            temp_results.loc[pd.Timestamp.date(current_ts)] = tmp

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
            if Field.Crop.harvest(current_ts) == True:

                Field.Crop.plant_date = None
                Field.Crop.planted = False
                Field.season_ended = True

                ts = pd.Timestamp.date(current_ts)      

                #Calculate and record estimated seasonal yield (SSM = 30% of summer rainfall as in Oliver et al. 2009)
                ssm = summer_rainfall['rainfall'].sum() * 0.30

                plant_available_water = Field.Soil.calcRAW(Field.Soil.current_TAW_mm, fraction=Field.Crop.depletion_fraction)

                #print "Scaling Factor", Field.Crop.scaling_factor
                #No crop yield if irrigation is not implemented
                if Field.Irrigation.implemented == False:
                    crop_yield = 0
                    temp_results.loc[ts, "P+I Crop Yield (t/Ha)"] = crop_yield
                    temp_results.loc[ts, "P Crop Yield (t/Ha)"] = crop_yield
                else:
                    crop_yield = Manager.calcPotentialCropYield(ssm, (total_effective_rainfall[Field.name] + ((Field.water_applied / Field.area) * 100)), Field.Crop.et_coef, Field.Crop.wue_coef, plant_available_water, Field.Crop.scaling_factor)
                    temp_results.loc[ts, "P+I Crop Yield (t/Ha)"] = crop_yield
                    crop_yield = Manager.calcPotentialCropYield(ssm, total_effective_rainfall[Field.name], Field.Crop.et_coef, Field.Crop.wue_coef, plant_available_water, Field.Crop.scaling_factor)
                    temp_results.loc[ts, "P Crop Yield (t/Ha)"] = crop_yield

                #If irrigation is not implemented, then forego profit and include implementation cost
                #TODO: CLEAN ALL THIS UP, MOVE RELEVANT PARTS TO FINANCE CLASS
                if Field.Irrigation.implemented == True:
                    #Calculate average cost across area, divided by number of fields to get average cost across entire farm
                    water_costs_per_Ha = sum(map(lambda WS: \
                        WS.calcTotalCostsPerHa(\
                            (Field.water_applied * water_source_proportion[WS.name]) / Field.area, Field.area) / len(Manager.Farm.fields), \
                            Manager.Farm.water_sources)\
                        )

                    irrig_costs_per_Ha = Field.Irrigation.calcTotalCostsPerHa()

                    costs = (water_costs_per_Ha + Field.Crop.variable_cost_per_Ha + irrig_costs_per_Ha + (pumping_costs[Field.name]/Field.area)) #* Field.area

                    profit = (temp_results.loc[ts, "P+I Crop Yield (t/Ha)"] * Field.Crop.price_per_yield)
                else:
                    irrig_costs_per_Ha = Field.Irrigation.calcTotalCostsPerHa()
                    water_costs_per_Ha = sum(map(lambda WS: WS.yearly_costs / Field.area, Manager.Farm.water_sources))
                    pump_maintenance_costs = sum(map(lambda WS: WS.Pump.calcOperationalCostPerHa(Field.area), Manager.Farm.water_sources))
                    costs = (irrig_costs_per_Ha + water_costs_per_Ha + pump_maintenance_costs)
                    profit = 0.0
                    Field.Irrigation.implemented = True
                #End if

                # print current_ts
                # print "Area:", Field.area
                # print "Crop:", Field.Crop.name
                # print "Water Used (ML): ", Field.water_applied
                # print "Proportions:"
                # print "    ", water_source_proportion
                # print "Water Costs ($/Ha): ", water_costs_per_Ha
                # print "    Including Pump maintenance ($/Ha): ", map(lambda WS: WS.Pump.calcTotalCostsPerHa(Field.area), Manager.Farm.water_sources)
                # print "    Implementation Cost included? ", map(lambda WS: WS.implemented == False, Manager.Farm.water_sources)
                # print "Water Cost Breakdown:"
                # print "    ", map(lambda WS: \
                #     WS.calcTotalCostsPerHa(\
                #         (Field.water_applied * water_source_proportion[WS.name]) / Field.area, Field.area) / len(Manager.Farm.fields), \
                #         Manager.Farm.water_sources)
                # print "V Costs ($/Ha): ", Field.Crop.variable_cost_per_Ha
                # print "Pumping Costs ($/Ha): ", (pumping_costs[Field.name]/Field.area)
                # print "Irrigation ($/Ha): ", irrig_costs_per_Ha
                # print "  Implementation: ", Field.Irrigation.cost_per_Ha
                # print "Gross Income per Ha:", profit * Field.Crop.price_per_yield
                # print "GM ($/Ha):", profit - costs
                # print "----------------------\n"  

                temp_results.loc[ts, "Total Field Profit ($/Ha)"] = profit - costs
                temp_results.loc[ts, "Annualised Field Profit ($/Ha)"] = Manager.Finance.annualizeCapital(temp_results.loc[ts, "Total Field Profit ($/Ha)"], num_years=year_counter)

                temp_results.loc[ts, "SSM (mm)"] = ssm

                season_start_end = Field.Crop.getSeasonStartEnd(current_ts)
                s, e = season_start_end
                temp_results.loc[ts, "Seasonal Rainfall (mm)"] = Climate.getSeasonalRainfall([s, e], data=ClimateData[['rainfall']])

                total_effective_rainfall[Field.name] = 0
                total_water_applied[Field.name] = 0
                Field.water_applied = 0

            #End if

        #End field loop

        #Check that all Fields have been harvested
        harvest_counter = 0
        assert current_ts.year <= Manager.season_start_year+5, "Current season should not be outside last season end (current season year should have been updated)!"

        if Manager.season_started and (current_ts >= pd.to_datetime("{y}-{m}-{d}".format(y=Manager.season_start_year+1, m=end_date.month, d=end_date.day))):
            for Field in Manager.Farm.fields:
                if Field.season_ended:
                    harvest_counter += 1

                    #Do not include implementation costs in future calculations
                    if Field.Irrigation.implemented == False:
                        Field.Irrigation.implemented = True
                    #End if
                #End if

            #End for

            #If all fields have been harvested
            if harvest_counter == len(Manager.Farm.fields):
                if DEBUG:
                    print "Season Ended!"
                #End if
                Manager.season_started = False

                #Debugging counter
                season_counter = 0

                year_counter += 1

                #Reset pumping costs for next timestep
                for f in Manager.Farm.fields:
                    pumping_costs[f.name] = 0
            #End if
        #End if

        assert pd.to_datetime(str(timestep)) == current_ts, "Somehow the timestep changed! {} - {}".format(timestep, current_ts)

        timestep = loop_timestep

    #End while

    #print long_results
    # OUTPUT RESULTS ABOVE INTO CSV FOR VISUALIZATION
    for Field in Manager.Farm.fields:
        long_results[Field.name].loc['Total', :] = long_results[Field.name].sum(axis=0, numeric_only=True, skipna=False)
        FileHandler.writeCSV(long_results[Field.name], 'output', '2nd_phase_{f}.csv'.format(f=Field.name))
        FileHandler.writeCSV(irrigation_log[Field.name], 'output', '2nd_phase_{f}_irrig_log.csv'.format(f=Field.name))
    #End for

    print "==== DONE ===="

