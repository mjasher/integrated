## the first line to run for fish model
import os
import numpy as np

if __name__ == '__main__':
    #import os
    os.chdir('C:\\UserData\\fub\\work09\\MDB')

    from integrated.Modules.Core.Handlers.FileHandler import FileHandler
    from integrated.Modules.Ecology.FishFlow import FishFlow
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
    
    flow_data_path = "integrated/Modules/Ecology/Inputs/Hydrology/sce1/406265.csv" #201,202, 265
    # flow_data_path = dev_data_path+"/Hydrology/sce1/406202.csv"

    flow_data = FileHandle.loadCSV(flow_data_path, index_col="Date", parse_dates=True, dayfirst=True)
    flow_data[flow_data<0] = np.nan
    
    flow_col = "Flow"

    #import environmental flow requirement data
    eflow_req_path = "integrated/Modules/Ecology/Inputs/Ecology/Fish_flow_req.csv"
#    eflow_req_path = "Inputs/Ecology/Fish_flow_req.csv"
    eflow_req = FileHandle.loadCSV(eflow_req_path)

    # minimum duration requirements for low flow index
    summerlowday = 120
    winterlowday = 60 #winter low is limiting the low flow index -> u/c required
    
    # inputs for food index and dispersal index
    durations = {
        "spawning": 2,
        "dispersal": 2,
        "washout": 2
    }
    
    frequencies = {
        "spawning": 1,
        "dispersal": 1,
        "washout": 1
    }

    Fish = FishFlow()

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
    annual_flow = flow_data[flow_data.index >= '1970-06-01']
    annual_flow = annual_flow.resample("A", how='sum')
    flow_33 = annual_flow.quantile(q=0.33)["Flow"]
    flow_66 = annual_flow.quantile(q=0.66)["Flow"]
    
    # model period
    flow_data = flow_data[flow_data.index >= '1970-06-01']
#    flow_data = flow_data[flow_data.index <= '1973-05-31']

    fishIndexes = pd.DataFrame()
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
            
            if annualflow <= flow_33: #TODO 33 percentile of annual flow over flow record from 1970 at gauge 406201, value need to revisit once have better historical data,   43658 for all flow record, 15687.49068 for flow from 1970
                climate_cond = 'dry'
            elif annualflow >= flow_66: #66 percentile of annual flow from 1970, value need to revisit, 164583 for all flow record, 110198.68072 for flow from 1970
                climate_cond = 'wet'
            else:
                climate_cond = 'average'
            
            summerlow = eflow_req[eflow_req['climate'] == climate_cond]['summer_low'].iloc[0]
            winterlow = eflow_req[eflow_req['climate'] == climate_cond]['winter_low'].iloc[0]
            
#            spawning = eflow_req[eflow_req['climate'] == climate_cond]['spawning'].iloc[0]
#            dispersal = eflow_req[eflow_req['climate'] == climate_cond]['dispersal'].iloc[0]
#            washout = eflow_req[eflow_req['climate'] == climate_cond]['washout'].iloc[0]
            
            freshes = {
                "spawning":eflow_req[eflow_req['climate'] == climate_cond]['spawning'].iloc[0],
                "dispersal":eflow_req[eflow_req['climate'] == climate_cond]['dispersal'].iloc[0],
                "washout":eflow_req[eflow_req['climate'] == climate_cond]['washout'].iloc[0]
            }
            
            next_june = pd.to_datetime(datetime.date(year+1, 6, 1))
            next_jan = pd.to_datetime(datetime.date(year+1, 1, 1))
            
            timing = {
                "spawning": {"start":pd.to_datetime(datetime.date(year, 9, 1)), 
                           "end":pd.to_datetime(datetime.date(year, 12, 1)) - timedelta(days=1)},
                "dispersal": {
                    "start": pd.to_datetime(datetime.date(year, 10, 1)),
                    "end": next_june - timedelta(days=1),
                },
                "washout": {
                    "start": pd.to_datetime(datetime.date(year, 10, 1)),
                    "end":pd.to_datetime(datetime.date(year, 12, 10))
#                    "end": next_jan - timedelta(days=1)
                }
            }
    
            
            lowflow_index = Fish.calcLowFlowIndex(year_data, flow_col, summerlow, winterlow, summerlowday, winterlowday)
            spawn_index, dispersal_index, washout_index = Fish.calcSpawnIndex(year_data, flow_col, freshes, durations, frequencies, timing)

            
            #fish_index = pd.DataFrame(index=["{y}/{s0}/{s1}-{y1}/{e0}/{e1}".format(y=year, y1=year+1, s0=start_time[0], s1=start_time[1], e0=end_time[0], e1=end_time[1])])
            fish_index = pd.DataFrame(index=["{y}/{s0}-{y1}/{e0}".format(y=year, y1=year+1, s0=start_time[0], e0=end_time[0])])
            fish_index['lowflow_index'] = lowflow_index
            fish_index['spawning_index'] = spawn_index            
            fish_index['dispersal_index'] = dispersal_index
            fish_index['washout_index'] = washout_index

#            fish_index['annualflow']=annualflow

            #Add to benchmark dataframe
            fishIndexes = fishIndexes.append(fish_index)

        #End if

    #End for
    fishIndexes['long_lived_fish_index']=fishIndexes.mean(axis=1)
    fishIndexes['short_lived_fish_index']=fishIndexes['lowflow_index']
    
    fishIndexes['short_lived_fish_rindex']=pd.rolling_mean(fishIndexes['short_lived_fish_index'],2)
    fishIndexes['long_lived_fish_rindex']=pd.rolling_mean(fishIndexes['long_lived_fish_index'],4)  

    print fishIndexes.describe()
    fishIndexes["short_lived_fish_rindex"].plot()
    fishIndexes["long_lived_fish_rindex"].plot()   

FileHandle.writeCSV(fishIndexes, "./Integrated/Modules/Ecology/Outputs", "fish_index.csv")

#FileHandle.writeCSV(flow_data, "./Integrated/Modules/Ecology/Outputs", "fish_flowdata.csv")
