## the first line to run for platypus model
import os
os.chdir('C:\\UserData\\fub\\work09\\MDB')

from integrated.Modules.Core.Handlers.FileHandler import FileHandler
from integrated.Modules.Ecology.PlatypusFlow import PlatypusFlow
import pandas as pd
#import datetime

#import flow dev data
FileHandle = FileHandler()

flow_data_path = "Integrated/Modules/Ecology/Inputs/Hydrology/flow202.csv"
flow_data = FileHandle.loadCSV(flow_data_path, index_col="Date", parse_dates=True, dayfirst=True)
flow_col = "Flow"

#import environmental flow requirement data
eflow_req_path = "Integrated/Modules/Ecology/Inputs/Ecology/param_default/Env_flow_obj.csv"
eflow_req = FileHandle.loadCSV(eflow_req_path)

climate_cond = 'dry' ## TODO after toy: need to link up to scenario data and identify climate condition: dry, average or wet
summerlow = eflow_req[eflow_req['climate'] == climate_cond]['summer_low'].iloc[0]
winterlow = eflow_req[eflow_req['climate'] == climate_cond]['winter_low'].iloc[0]
summerlowday = 150
winterlowday = 150
level_buffer = 1



#Season and season window in days of year
# season_start = 100
# burrow_window = 45
# season_end = 250
# risk_threshold = 5


Platypus = PlatypusFlow()

yearly_data = flow_data.groupby(flow_data.index.year) ## TODO before toy: need to group by "ecology year": 1Dec-31May, 1Jun-30Nov

#Each year has to have full year data for calculations to be made
data_points_per_year = yearly_data.count()
years_with_sufficient_data = data_points_per_year[data_points_per_year[flow_col] >= 365].index.tolist()


###For testing only

#year = years_with_sufficient_data[125]
#year_data = flow_data[flow_data.index.year == year]
#yearly_flow_data=year_data
#summer_low_thd=summerlow
#winter_low_thd=winterlow

## end testing only


summer_index_thd=150
winter_index_thd=150

## for testing only: extract exmaple data between 2013-6-1 to 2014-5-31

#start = flow_data.index.searchsorted(datetime.datetime(2013,6,1))
#end = flow_data.index.searchsorted(datetime.datetime(2014,6,1))
#yearly_flow_data = flow_data.ix[start:end]

## end testing only

burrow_startmonth = 7
burrow_endmonth = 8
entrance_buffer = 10
breeding_startmonth = 9
breeding_endmonth = 2


platypusIndexes = pd.DataFrame()
for i, year in enumerate(years_with_sufficient_data):

	year_data = flow_data[flow_data.index.year == year]

	lowflow_index = Platypus.calcLowFlowIndex(year_data, flow_col, summerlow,winterlow,summerlowday,winterlowday)

## TODO after toy: two more indexes
		
	#food_index = 
		
	#dispersal_index = 
		
	burrow_index = Platypus.calcBurrowIndex(year_data, flow_col, burrow_startmonth, burrow_endmonth, entrance_buffer, breeding_startmonth, breeding_endmonth)
	
	platypus_index = pd.DataFrame(index=[year])
	platypus_index['lowflow_index'] = lowflow_index
#	platypus_index['food_index'] = food_index
#	platypus_index['dispersal_index'] = dispersal_index
	platypus_index['burrow_index'] = burrow_index

	#Add to benchmark dataframe
	platypusIndexes = platypus_index.append(platypus_index)
	
#End for

print platypusIndexes


## TODO after toy: aggregation

