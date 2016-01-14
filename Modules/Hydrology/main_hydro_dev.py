#main_hydro_dev.py

from integrated.Modules.Core.Handlers.FileHandler import FileHandler
from Hydrology import Hydrology
import pandas as pd
import datetime

#Set up the file handler
FileHandle = FileHandler()

#Import all the files from the data directory
data_path = "data"
data = FileHandle.importFiles(data_path, ext=".csv", walk=False)
data = data["data"] #Remove parent directory from listing

#Create a Hydrology Object
Hydro = Hydrology(data)

#Define starting time and the end of scenario range
timestep = datetime.date(year=1900, month=1, day=1)
end_date = datetime.date(year=1900, month=2, day=1)
step = 1 #number of days for each timestep

#No starting values, could pass a Pandas dataframe with initial results
#expected Dataframe columns are node_id, calc_type (IHACRES, Routing, etc.), to_node, storage (initial water volume), prev_store
results = None

for ts in xrange(step, 365, step):

	loop_timestep = timestep + datetime.timedelta(days=ts)

	results = Hydro.run(loop_timestep, data=results)

	print results

	results['prev_storage'] = results['storage']
#End for


# #Get climate data for each node
# climate = {}
# for ID in data['network']['ID']:

# 	network_data = data['network']

# 	node_id = network_data[network_data['ID'] == ID]['node'].iloc[0]
# 	climate[node_id] = pd.DataFrame()
# 	climate[node_id]['rainfall'] = data['climate']["{ID}_rain".format(ID=ID)]
# 	climate[node_id]['evap'] = data['climate']["{ID}_evap".format(ID=ID)]
# 	# climate[node_id]['to_node'] = network_data[network_data['ID'] == ID]['to node'].iloc[0]

# 	print climate[node_id]






