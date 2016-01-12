#flow_dev.py

from FlowSuitability import FlowSuitability

from integrated.Modules.Core.Handlers.FileHandler import FileHandler

FileHandle = FileHandler()

#Paths to files
dev_data_path = "Namoi_DSS/Inputs"
scenarios = [dev_data_path+"/Hist"]

# Read in data
# read in all breakpoint files from 1900 til end of file
date_range = ["1900-01-01", None]
indexes = FileHandle.importFiles(dev_data_path+"/index", ext=".csv", walk=False)
indexes = indexes["index"] #Remove parent folder listing from Dict, as this is unneeded

# read in asset table
#This could be set as class attribute as it is used as a global in the R script
asset_table = FileHandle.loadCSV(dev_data_path+"/ctf_dss.csv")

# read in weights
weights = FileHandle.loadCSV(dev_data_path+"/index/weight/weight.csv")

#change headers to lowercase to make it consistent with other csvs
weights.columns = [x.lower() for x in weights.columns]

# Set up additional parameters:
# Set up weight for groundwater index
gweight = 0.2

# For DSS, can use RRGMS only as a minimum.
specieslist = ["RRGMS", "RRGRR", "BBMS", "BBRR", "LGMS", "LGRR", "WCMS", "WCRR"]

FlowIndexer = FlowSuitability(asset_table, specieslist, indexes, weights)

#This is unused at the moment
weighted = lambda d, gweight: d[1]*gweight + d[2]*(1-gweight)

for scenario_num in xrange(0, len(scenarios)):

	scen = scenarios[scenario_num]

	scenario_data = FileHandle.importFiles(scen, index_col="Date", parse_dates=True, date_range=date_range)

	#For each asset, generate flow indexes for each species
	for j in xrange(0, len(asset_table.index)):
		flow_indexes = FlowIndexer.generateEnvIndex(asset_id=j, scen_data=scenario_data, ecospecies=specieslist) #, gswfun=weighted

		#For development purposes only. Display index results for each species
		print "Asset {id}".format(id=j+1)
		for species in specieslist:
			print species
			print "---- Groundwater ----"
			print flow_indexes[species]['gw']
			print "---------------------"
			print "---- Surface Water ----"
			print flow_indexes[species]['sw']
			print "---------------------"
			print "---- Water Index ----"
			print flow_indexes[species]['water_index']
			print "---------------------"
		#End for

		#Save indexes to file or something?

	#End for

#End for

