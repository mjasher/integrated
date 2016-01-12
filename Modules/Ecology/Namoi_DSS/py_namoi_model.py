from __future__ import division
import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

from scipy.interpolate import interp1d

from integrated.Modules.Core.Handlers.FileHandler import FileHandler

"""

Initial attempt at converting R script into Python. This should not be used in production

NOTE: Paths are relative to this script unless otherwise stated/indicated
"""

def ceaseDays(df, **kwargs):

	"""
	Determine the number of days flow stopped
	"""

	ceaseflow = lambda x: x.dropna()[x == 0].count()

	grouping = df.groupby(df.index.year)

	return grouping.apply(ceaseflow)
#End ceaseDays()

	

#End ceaseDays()

def flowSummary(df, func_name):

	"""
	Calculate summary statistics (defined by function).

	:param df: Pandas dataframe, must have datetime index
	:param func_name: statistical attribute as found in Python pandas: min, max, median, etc.
	:date_start: Date to 

	"""

	grouping = df.groupby(df.index.year)
	
	func = getattr(grouping, func_name)
	return func()

#End flowSummary()

def ctfDays(df, ctf=4000, **kwargs):

	flooddays = lambda x, ctf: x.dropna()[x > ctf].count() #[x > ctf].count()

	#Original R code:
	#summaryby <- as.POSIXlt(time(x))$year + 1900
	#Gets number of years since 1900, then adds 1900 years
	grouping = df.groupby(df.index.year)

	return grouping.apply(func=flooddays, ctf=ctf)
#End ctfDays

## Function to calculate annual averaged number of overflow (flow above a threshold) events. Input (x) is surfaceflow
## By default, the minimum number of days that can separate events is 5 days,
## and the minimum number of days in each event window is 1 day.
# ctf.events <- function (x, ctf = 4000, gap = 5, minduration = 1, ...){
#   flowevent <- eventseq(x, thresh = ctf, mingap = gap, mindur=minduration)
#   floweventinfo <- eventinfo(x, flowevent, FUN=mean)
#   annualevent <- aggregate(Value ~ Yearmid, data=floweventinfo, FUN=length)
#   eventyear <- as.POSIXlt(as.Date(as.character(annualevent[,1]), format="%Y"))$year+1900
#   annualeventzoo <- zoo(annualevent[,2],eventyear)
#   return(annualeventzoo)
# }

def eventseq(flow_df, threshold=4000, max_separation=5, min_duration=1):

	"""
	Determine flow events

	:param threshold: Threshold

	:Returns: Pandas DataFrame 
		start: event start date
		end: event end date
		duration: Duration of event
		dry_period: Preceeding dry period
		timing: 1-12, representing month of event start (1 = Jan, 12 = December)
	"""

	temp_df = pd.DataFrame(data=flow_df, index=flow_df.index)
	col = temp_df.columns[0]

	temp_df['datetime'] = temp_df.index

	#If value is below threshold and the time distance between flow observation is <= max_separation, and the flow time is >= min_duration, count as event
	high_flows = temp_df[temp_df.Flow >= threshold]

	# high_flows.plot()
	# plt.show()

	high_flow_events = high_flows[ \
						(high_flows['datetime'].diff() <= pd.Timedelta(days=max_separation)) \
						& (high_flows.datetime.diff() >= pd.Timedelta(days=min_duration)) \
						].copy()

	# print high_flow_events

	#Return empty dataframe if no events found
	if len(high_flow_events.index) == 0:
		return pd.DataFrame()

	separate_events = ((high_flow_events.datetime.diff() <= np.timedelta64(max_separation, "D")) ) #| (high_flow_events.datetime.diff().isnull()

	#Get all places that are False (start of events)
	starts = (separate_events == False)

	#Find the end of event; previous row from False rows
	ends = (starts.shift(-1) == True)

	#Set last record to be the end, so that the number of event starts matches with number of event ends
	ends.iloc[-1] = True 
	
	#mark start and end for each event
	high_flow_events.loc[starts, 'start'] = True
	high_flow_events.loc[ends, 'end'] = True

	events = pd.DataFrame()
	events['start'] = starts[starts == True].index
	events['end'] = ends[ends == True].index
	events['duration'] = events['end'] - events['start']
	events['dry_period'] = events['start'] - events['end'].shift(1)
	events['timing'] = events['start'].map(lambda x: x.to_datetime().month)

	return events

#End eventseq()


def ctfEvents(df, ctf=4000, gap=5, min_duration=1, **kwargs):

	# print eventseq(df)
	print "----------------------"

	# flowevent <- eventseq(x, thresh = ctf, mingap = gap, mindur=minduration)
	# floweventinfo <- eventinfo(x, flowevent, FUN=mean)
	# annualevent <- aggregate(Value ~ Yearmid, data=floweventinfo, FUN=length)
	# eventyear <- as.POSIXlt(as.Date(as.character(annualevent[,1]), format="%Y"))$year+1900
	# annualeventzoo <- zoo(annualevent[,2],eventyear)
	# return(annualeventzoo)
	
#End ctfEvents()

# df = pd.DataFrame(dict(x=[10, 20, 30, 0, 0, 0, 0, 0]))

# ceaseflow = lambda x: (x == 0).sum()

# print ceaseflow(df)

weighted = lambda d, gweight: d[1]*gweight + d[2]*(1-gweight)

def getAssetParam(asset_table, gauge, col):

	return asset_table[asset_table["Gauge"] == int(gauge)][col].iloc[0]



def envIndex(asset_table, asset_id, scenario, scen_data, ecospecies, **kwargs):

	gauge = str(asset_table["Gauge"][asset_id])

	surfaceflow = scen_data[gauge]["Flow"]
	baseflow = scen_data[gauge]["Baseflow"]

	#Get GW level data with datetime
	gw_level = scen_data["gwlevel"][["A{a}".format(a=asset_id+1)]]

	gw_mean = flowSummary(gw_level, "mean")
	baseflow_median = flowSummary(gw_level, "median")
	num_days_flow_ceased = ceaseDays(surfaceflow)
	total_flow = flowSummary(surfaceflow, "sum")

	# print asset_table["Gauge"] == gauge #["CTF_low"]

	#get first row out of matching rows
	low_ctf = getAssetParam(asset_table, gauge, "CTF_low")
	ctf_low_days = ctfDays(surfaceflow, ctf=low_ctf)
	ctf_low_events = ctfEvents(surfaceflow)
	
	mid_ctf = getAssetParam(asset_table, gauge, "CTF_mid")
	ctf_mid_days = ctfDays(surfaceflow, ctf=mid_ctf)
	ctf_mid_events = ctfEvents(surfaceflow)

	high_ctf = getAssetParam(asset_table, gauge, "CTF_high")
	ctf_high_days = ctfDays(surfaceflow, ctf=high_ctf)
	ctf_high_events = ctfEvents(surfaceflow)

	#(flow_df, threshold=4000, max_separation=5, min_duration=1)
	flowevent = eventseq(surfaceflow, \
		threshold=getAssetParam(asset_table, gauge, 'Event_threshold'), \
		max_separation=getAssetParam(asset_table, gauge, 'Event_gap'), \
		min_duration=getAssetParam(asset_table, gauge, 'Event_dur') )

	
#End envIndex()


# ## Function to calculate median/total flow/baseflow levels (annual), if total, fun=sum.
# flowsum <- function (x,fun=median,...){
#   summaryby <- as.POSIXlt(time(x))$year + 1900
#   flowsummary <- aggregate(x, by=summaryby, FUN = fun, na.rm=TRUE)
#   return(round(flowsummary,2))
# }


### Script starts here ###

FileHandle = FileHandler()

#Read in input data

## Read in input data

# read in all breakpoint files from 1900 til end of file
date_range = ["1900-01-01", None]
indexes = FileHandle.importFiles("Inputs/index", ext=".csv", walk=False)

# read in asset table
#This could be set as class attribute as it is used as a global in the R script
asset_table = FileHandle.loadCSV("Inputs/ctf_dss.csv")

# read in weights
weightall = FileHandle.loadCSV("Inputs/index/weight/weight.csv")

# Set up additional parameters:
# Set up weight for groundwater index
gweight = 0.2

#scenarios = FileHandle.getFolders('Inputs/')
scenarios = ["Inputs/Hist"] #FileHandle.getFolders('Inputs/')

# For DSS, can use RRGMS only as a minimum.
specieslist = ["RRGMS", "RRGRR", "BBMS", "BBRR", "LGMS", "LGRR", "WCMS", "WCRR"] 


for scenario_num in xrange(0, len(scenarios)):

	scen = scenarios[scenario_num]
	# scenario_files = FileHandle.getFileList(scen)

	scenario_data = FileHandle.importFiles(scen, index_col="Date", parse_dates=True, date_range=date_range)

	#For each dataset, 

	# asset_table, asset_id, scenario, scen_data, ecospecies, **kwargs

	for j in xrange(0, len(asset_table.index)):
		index_all = envIndex(asset_table=asset_table, asset_id=j, scenario=scen, scen_data=scenario_data, ecospecies=specieslist, gswfun=weighted)

		# print "End"
		# print index_all
		# write.zoo(index.all, file=paste("Outputs\\", scenariolist[i],"\\asset", j,".csv", sep=""),sep=",")



#End for


# class EcologicalSystem(component):

# 	def __init__(self, index_data, scen_data, asset_data, weights, gweight=0.2):
# 		pass
# 	#End init()


