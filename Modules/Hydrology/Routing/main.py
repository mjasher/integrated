from integrated.Modules.Core.Handlers.FileHandler import FileHandler
from integrated.Modules.Hydrology.Routing.Routing import Routing
import pandas as pd

ClimateData = FileHandler().loadCSV('test_data/climate/Echuca.txt', columns=[0, 7, 9], skiprows=41, delimiter=r'\s*', engine='python') #
ClimateData.index = pd.to_datetime(ClimateData[ClimateData.columns[0]], format='%Y%m%d')
ClimateData.columns = ['Date', 'rainfall', 'ET']

WaterRouter = Routing(ClimateData, 50)

prev_storage = 50
inflow = 100
irrig_out = 25
evap = 10
local_inflow = 10
base_flow = 5
deep_drainage = 10
storage_coef = 0.5
ET_f = 1.1

print WaterRouter.calcFlow(prev_storage, inflow, irrig_out, evap, local_inflow, base_flow, deep_drainage, storage_coef, ET_f)