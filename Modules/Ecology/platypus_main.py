## the first line to run for platypus model
import os
os.chdir('C:\\UserData\\fub\\work09\\MDB')

from integrated.Modules.Core.Handlers.FileHandler import FileHandler
from integrated.Modules.Ecology.PlatypusFlow import PlatypusFlow
import pandas as pd

#import flow dev data
FileHandle = FileHandler()

flow_data_path = "Integrated/Modules/Ecology/Inputs/Hydrology/flow202.csv"
flow_data = FileHandle.loadCSV(flow_data_path, index_col="Date", parse_dates=True)
flow_col = "Flow"

#import environmental flow requirement data
eflow_req_path = "Integrated/Modules/Ecology/Inputs/Ecology/param_default/Env_flow_obj.csv"
eflow_req = FileHandle.loadCSV(eflow_req_path)

climate_cond = 'dry'
summerlow = eflow_req[eflow_req['climate'] == climate_cond]['summer_low']
winterlow = eflow_req[eflow_req['climate'] == climate_cond]['winter_low']
summerlowday = 150
winterlowday = 150



#Season and season window in days of year
# season_start = 100
# burrow_window = 45
# season_end = 250
# level_buffer = 1
# risk_threshold = 5



Platypus = PlatypusFlow()

yearly_data = flow_data.groupby(flow_data.index.year)

#Each year has to have enough data for calculations to be made
data_points_per_year = yearly_data.count()
years_with_sufficient_data = data_points_per_year[data_points_per_year[flow_col] > season_end].index.tolist()

benchmarks = pd.DataFrame()
for i, year in enumerate(years_with_sufficient_data):

	year_data = flow_data[flow_data.index.year == year]
	drowning_benchmarks = Platypus.calcFlowBenchmark(year_data, flow_col, season_start, burrow_window, season_end, level_buffer)

	drowning_benchmarks.loc[drowning_benchmarks.index == year, 'low_flow_risk'] = Platypus.calcLowFlowIndex(year_data, flow_col, summerlow,winterlow,summerlowday,winterlowday)

	#Add to benchmark dataframe
	benchmarks = benchmarks.append(drowning_benchmarks)
	
#End for

print benchmarks


