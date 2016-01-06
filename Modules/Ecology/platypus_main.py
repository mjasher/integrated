from integrated.Modules.Core.Handlers.FileHandler import FileHandler
from integrated.Modules.Ecology.PlatypusFlow import PlatypusFlow

#import flow dev data
FileHandle = FileHandler()

flow_data_path = "Namoi_DSS/Inputs/Hist/419001.csv"
flow_data = FileHandle.loadCSV(flow_data_path, index_col="Date", parse_dates=True)

#Season and season window in days of year
season_start = 100
burrow_window = 45
season_end = 250
level_buffer = 1
risk_threshold = 5

flow_col = "Flow"

Platypus = PlatypusFlow()

yearly_data = flow_data.groupby(flow_data.index.year)

#Each year has to have enough data for calculations to be made
data_points_per_year = yearly_data.count()
years_with_sufficient_data = data_points_per_year[data_points_per_year["Flow"] > season_end].index.tolist()

benchmarks = {}
for i, year in enumerate(years_with_sufficient_data):

	year_data = flow_data[flow_data.index.year == year]
	drowning_benchmarks = Platypus.calcFlowBenchmark(year_data, flow_col, season_start, burrow_window, season_end, level_buffer)

	benchmarks[year] = drowning_benchmarks

	benchmarks[year]['habitat_risk'] = Platypus.calcHabitatRisk(year_data, flow_col, risk_threshold)
#End for

print benchmarks


