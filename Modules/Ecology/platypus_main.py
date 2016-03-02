## the first line to run for platypus model
import os
import numpy as np

if __name__ == '__main__':
    #import os
    os.chdir('C:\\UserData\\fub\\work09\\MDB')

    from integrated.Modules.Core.Handlers.FileHandler import FileHandler
    from integrated.Modules.Ecology.PlatypusFlow import PlatypusFlow
    import pandas as pd

    # to plot in seperate window
    #%matplotlib qt

    #import flow dev data
    FileHandle = FileHandler()
    #Paths to files
    dev_data_path = "integrated/Modules/Ecology/Inputs"
    # dev_data_path = "Inputs"

    # Read in flow data
    
    flow_data_path = "integrated/Modules/Ecology/Inputs/Hydrology/sce1/406201.csv"
    # flow_data_path = dev_data_path+"/Hydrology/sce1/406202.csv"

    flow_data = FileHandle.loadCSV(flow_data_path, index_col="Date", parse_dates=True, dayfirst=True)
    flow_data[flow_data<0] = np.nan
    
    flow_col = "Flow"

    #import environmental flow requirement data
    eflow_req_path = "integrated/Modules/Ecology/Inputs/Ecology/Env_flow_obj.csv"
#    eflow_req_path = "Inputs/Ecology/Env_flow_obj.csv"
    eflow_req = FileHandle.loadCSV(eflow_req_path)

    # inputs for low flow index
    summerlowday = 120
    winterlowday = 60 #winter low is limiting the low flow index -> u/c required
    
    # input for food index and dispersal index
    summerdur = 1
    autumndur = 2
    summerfreq = 1
    autumnfreq = 2


    Platypus = PlatypusFlow()

#    scenarios = [dev_data_path+"/Hydrology/sce1", dev_data_path+"/Hydrology/sce2"]
#    date_range = ["1900-01-01", None]
    
#    for scenario_dir in xrange(0, len(scenarios)):
#
#        scen = scenarios[scenario_dir]
#
#        scen_name = scen.split('/')[-1]
#
#        scenario_data = FileHandle.importFiles(scen, index_col="Date", parse_dates=True, date_range=date_range, dayfirst=True)
        
    #Get all the years in flow data
    yearly_data = flow_data.groupby(flow_data.index.year) 
    years_in_data = yearly_data.count()
    years_in_data = years_in_data.index.tolist()

    # print years_in_data

    # Example ecological year
    # Could read these in from a collection of CSVs?
    # Looks like 
    #       day, month
    #start    1, 6
    #end     31, 5
    hydro_years = pd.DataFrame({
        'month': [6, 5],
        'day': [1, 31]
    }, index=['start', 'end'])

    #print hydro_years

    burrow_startmonth = 7
    burrow_endmonth = 8
    entrance_buffer = 30 #ML/day
    breeding_startmonth = 9
    breeding_endmonth = 2

    import datetime

#dev_data_path = "Integrated/Modules/Ecology/Inputs"
#scenarios = [dev_data_path+"/Hydrology/sce1", dev_data_path+"/Hydrology/sce2"]
#date_range = ["1900-01-01", None]
#
#for scenario_dir in xrange(0, len(scenarios)):
#
#   scen = scenarios[scenario_dir]
#
#   scen_name = scen.split('/')[-1]
#
#   scenario_data = FileHandle.importFiles(scen, index_col="Date", parse_dates=True, date_range=date_range, dayfirst=True) #
# 

    flow_data = flow_data[flow_data.index >= '1970-06-01']
#    flow_data = flow_data[flow_data.index <= '1973-05-31']

    platypusIndexes = pd.DataFrame()
    for year in years_in_data:

        start_time = (hydro_years.loc['start', 'month'], hydro_years.loc['start', 'day'])
        end_time = (hydro_years.loc['end', 'month'], hydro_years.loc['end', 'day'])

        start = flow_data.index.searchsorted(datetime.datetime(year, start_time[0], start_time[1]))
        end = flow_data.index.searchsorted(datetime.datetime(year+1, end_time[0], end_time[1]))

        year_data = flow_data.ix[start:end]

        #Calculate indexes if there is enough data for the ecological year
        if len(year_data) >= 363:
            # identify climate condition and extract flow thresholds
            annualflow = year_data['Flow'].sum()
            
            if annualflow <= 15687: #TODO 33 percentile of annual flow over flow record from 1970, value need to revisit once have better historical data,   43658 for all flow record, 15687.49068 for flow from 1970
                climate_cond = 'dry'
            elif annualflow >= 110199: #66 percentile of annual flow from 1970, value need to revisit, 164583 for all flow record, 110198.68072 for flow from 1970
                climate_cond = 'wet'
            else:
                climate_cond = 'average'
            
            summerlow = eflow_req[eflow_req['climate'] == climate_cond]['summer_low'].iloc[0]
            winterlow = eflow_req[eflow_req['climate'] == climate_cond]['winter_low'].iloc[0]
            fresh = eflow_req[eflow_req['climate'] == climate_cond]['fresh'].iloc[0]
    
            
            lowflow_index = Platypus.calcLowFlowIndex(year_data, flow_col, summerlow, winterlow, summerlowday, winterlowday)
            food_index, dispersal_index = Platypus.calcFoodDispIndex(year_data, flow_col, fresh, summerdur, autumndur, summerfreq, autumnfreq)
            burrow_index = Platypus.calcBurrowIndex(year_data, flow_col, burrow_startmonth, burrow_endmonth, entrance_buffer, breeding_startmonth, breeding_endmonth)
            
            #platypus_index = pd.DataFrame(index=["{y}/{s0}/{s1}-{y1}/{e0}/{e1}".format(y=year, y1=year+1, s0=start_time[0], s1=start_time[1], e0=end_time[0], e1=end_time[1])])
            platypus_index = pd.DataFrame(index=["{y}/{s0}-{y1}/{e0}".format(y=year, y1=year+1, s0=start_time[0], e0=end_time[0])])
            platypus_index['lowflow_index'] = lowflow_index
            platypus_index['food_index'] = food_index
            platypus_index['dispersal_index'] = dispersal_index
            platypus_index['burrow_index'] = burrow_index
#            platypus_index['annualflow']=annualflow

            #Add to benchmark dataframe
            platypusIndexes = platypusIndexes.append(platypus_index)

        #End if

    #End for
    platypusIndexes['platypus_index']=platypusIndexes.mean(axis=1)
    platypusIndexes['platypus_rolling_index']=pd.rolling_mean(platypusIndexes['platypus_index'],3)

    print platypusIndexes.describe()

FileHandle.writeCSV(platypusIndexes, "./Integrated/Modules/Ecology/Outputs", "platypus_index.csv")

FileHandle.writeCSV(flow_data, "./Integrated/Modules/Ecology/Outputs", "platypus_flowdata.csv")



    ###For testing only

    #year = years_with_sufficient_data[125]
    #year_data = flow_data[flow_data.index.year == year]
    #yearly_flow_data=year_data
    #summer_low_thd=summerlow
    #winter_low_thd=winterlow

    ## end testing only


    # summer_index_thd=150
    # winter_index_thd=150

    # ## for testing only: extract exmaple data between 2013-6-1 to 2014-5-31
    # import datetime
    # start = flow_data.index.searchsorted(datetime.datetime(2013,6,1))
    # end = flow_data.index.searchsorted(datetime.datetime(2014,6,1))
    # # yearly_flow_data = flow_data.ix[start:end]
    # flow_data = flow_data.ix[start:end]
    # years_with_sufficient_data = [2013, 2014]

    # ## end testing only

    # burrow_startmonth = 7
    # burrow_endmonth = 8
    # entrance_buffer = 10
    # breeding_startmonth = 9
    # breeding_endmonth = 2


    # platypusIndexes = pd.DataFrame()
    # for i, year in enumerate(years_with_sufficient_data):

    #   year_data = flow_data[flow_data.index.year == year]

    #   lowflow_index = Platypus.calcLowFlowIndex(year_data, flow_col, summerlow,winterlow,summerlowday,winterlowday)

    # ## TODO after toy: two more indexes
            
    #   #food_index = 
            
    #   #dispersal_index = 
            
    #   burrow_index = Platypus.calcBurrowIndex(year_data, flow_col, burrow_startmonth, burrow_endmonth, entrance_buffer, breeding_startmonth, breeding_endmonth)
        
    #   platypus_index = pd.DataFrame(index=[year])
    #   platypus_index['lowflow_index'] = lowflow_index
    # # platypus_index['food_index'] = food_index
    # # platypus_index['dispersal_index'] = dispersal_index
    #   platypus_index['burrow_index'] = burrow_index

    #   #Add to benchmark dataframe
    #   platypusIndexes = platypus_index.append(platypus_index)
        
    # #End for

    # print platypusIndexes


    # ## TODO after toy: aggregation

