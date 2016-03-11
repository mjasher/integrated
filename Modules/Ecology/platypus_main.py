## the first line to run for platypus model
import os
import numpy as np

if __name__ == '__main__':
    #import os
    os.chdir('C:\\UserData\\fub\\work09\\MDB')

    from integrated.Modules.Core.Handlers.FileHandler import FileHandler
    from integrated.Modules.Ecology.PlatypusFlow import PlatypusFlow
#    from integrated.Modules.Ecology.SpeciesFlow import SpeciesFlow
    import pandas as pd
    import datetime
    from datetime import timedelta

    #import flow dev data
    FileHandle = FileHandler()
    #Paths to files
    dev_data_path = "integrated/Modules/Ecology/Inputs"
    # dev_data_path = "Inputs"

    # Read in flow data
    
    flow_data_path = "integrated/Modules/Ecology/Inputs/Hydrology/sce1/406201.csv" #201,202, 265
    # flow_data_path = dev_data_path+"/Hydrology/sce1/406202.csv"

    flow_data = FileHandle.loadCSV(flow_data_path, index_col="Date", parse_dates=True, dayfirst=True)
    flow_data[flow_data<0] = np.nan
    
    flow_col = "Flow"

    #import environmental flow requirement data
    eflow_req_path = "integrated/Modules/Ecology/Inputs/Ecology/Platypus_flow_req.csv"
#    eflow_req_path = "Inputs/Ecology/Platypus_flow_req.csv"
    eflow_req = FileHandle.loadCSV(eflow_req_path)

    # minimum duration requirements for low flow index
    summerlowday = 120
    winterlowday = 60 #winter low is limiting the low flow index -> u/c required
    
    # inputs for food index and dispersal index
    durations = {
        "summerfood": 1,
        "autumnfood": 2,
        "dispersal": 2
    }
    
    frequencies = {
        "summerfood": 1,
        "autumnfood": 2,
        "dispersal": 2
    }

    # inputs for burrow index
    burrow_startmonth = 7
    burrow_endmonth = 8
    entrance_buffer = 30 #ML/day
    breeding_startmonth = 9
    breeding_endmonth = 2

    Platypus = PlatypusFlow()

    #Get all the years in flow data
    yearly_data = flow_data.groupby(flow_data.index.year) 
    years_in_data = yearly_data.count()
    years_in_data = years_in_data.index.tolist()

    # define ecology year
    ecology_year = pd.DataFrame({
        'month': [6, 5],
        'day': [1, 31]
    }, index=['start', 'end'])

    #print ecology_year

    # calcualte flow thresholds for calculating climate condition
    flow_data = flow_data[flow_data.index >= '1970-06-01']
    annual_flow = flow_data.resample("A", how='sum')
    flow_33 = annual_flow.quantile(q=0.33)["Flow"]
    flow_66 = annual_flow.quantile(q=0.66)["Flow"]
    
    
    # model period
    flow_data = flow_data[flow_data.index >= '1970-06-01']
#    flow_data = flow_data[flow_data.index <= '1973-05-31']
    

    platypusIndexes = pd.DataFrame()
    for year in years_in_data:

        start_time = (ecology_year.loc['start', 'month'], ecology_year.loc['start', 'day'])
        end_time = (ecology_year.loc['end', 'month'], ecology_year.loc['end', 'day'])

        start = flow_data.index.searchsorted(datetime.datetime(year, start_time[0], start_time[1]))
        end = flow_data.index.searchsorted(datetime.datetime(year+1, end_time[0], end_time[1]))

        year_data = flow_data.ix[start:end]

        #Calculate indexes if there is enough data for the ecological year
        if len(year_data) >= 363:
            # identify climate condition and extract flow thresholds
            annualflow = year_data['Flow'].sum()
            
            if annualflow <= flow_33: #TODO 33 percentile of annual flow over flow record from 1970, value need to revisit once have better historical data,   43658 for all flow record, 15687.49068 for flow from 1970
                climate_cond = 'dry'
            elif annualflow >= flow_66: #66 percentile of annual flow from 1970, value need to revisit, 164583 for all flow record, 110198.68072 for flow from 1970
                climate_cond = 'wet'
            else:
                climate_cond = 'average'
            
            summerlow = eflow_req[eflow_req['climate'] == climate_cond]['summer_low'].iloc[0]
            winterlow = eflow_req[eflow_req['climate'] == climate_cond]['winter_low'].iloc[0]
#            fresh = eflow_req[eflow_req['climate'] == climate_cond]['fresh'].iloc[0]
            
            freshes = {
                "summerfood":eflow_req[eflow_req['climate'] == climate_cond]['fresh'].iloc[0],
                "autumnfood":eflow_req[eflow_req['climate'] == climate_cond]['fresh'].iloc[0],
                "dispersal":eflow_req[eflow_req['climate'] == climate_cond]['fresh'].iloc[0]
            }
            
            next_march = pd.to_datetime(datetime.date(year+1, 3, 1))
            next_june = pd.to_datetime(datetime.date(year+1, 6, 1))
            
            timing = {
                "summerfood": {"start":pd.to_datetime(datetime.date(year, 12, 1)), 
                           "end":next_march - timedelta(days=1)},
                "autumnfood": {
                    "start": next_march,
                    "end": next_june - timedelta(days=1),
                },
                "dispersal": {
                    "start": pd.to_datetime(datetime.date(year+1, 4, 1)),
                    "end": next_june - timedelta(days=1)
                }
            }
    
            
            lowflow_index = Platypus.calcLowFlowIndex(year_data, flow_col, summerlow, winterlow, summerlowday, winterlowday)
            food_index, dispersal_index = Platypus.calcFoodDispIndex(year_data, flow_col, freshes, durations, frequencies, timing)
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
    platypusIndexes["platypus_rolling_index"].plot(marker='o')
#    platypusIndexes.index.name = 'Time'
#    ggplot(platypusIndexes,aes(x='Time', y='platypus_rolling_index'))+geom_line()

FileHandle.writeCSV(platypusIndexes, "./Integrated/Modules/Ecology/Outputs", "platypus_index.csv")

FileHandle.writeCSV(flow_data, "./Integrated/Modules/Ecology/Outputs", "platypus_flowdata.csv")
