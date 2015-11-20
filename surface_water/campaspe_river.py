import os 
import sys
import numpy
import json
# bulk_site_dir = "/home/mikey/Desktop/aus-hydro-data/downloaded_data/data.water.vic/download.20151022110838/"
import matplotlib.pylab as plt

sys.path.append("/home/mikey/Desktop/aus-hydro-data/")
from fetch_data import utils, bom, vic_water_surface

def save_site(site_id):
	bulk_site_dir = "/home/mikey/Desktop/aus-hydro-data/downloaded_data/data.water.vic/download.20151022110838/"
	all_bom_sites_file = '/home/mikey/Desktop/aus-hydro-data/downloaded_data/stations.txt'
	zipped_sites_dir = '/home/mikey/Desktop/aus-hydro-data/downloaded_data/bom'

	# get levels and flows from data.vic.water
	# site_id = "405230"
	data_types = ["MeanWaterLevel", "MeanWaterFlow"]
	site_details, data_types_values = vic_water_surface.read_bulk_downloaded_sw_file(bulk_site_dir, site_id, data_types)
	dates = data_types_values["MeanWaterFlow"]["dates"]
	flows = data_types_values["MeanWaterFlow"]["data"]
	level_dates = data_types_values["MeanWaterLevel"]["dates"]
	levels = data_types_values["MeanWaterLevel"]["data"]
	
	lat, lng = (float(site_details["Latitude"]), float(site_details["Longitude"])) # TODO could use geofabric AHGFCatchment to find center of catchment 
	closest_names, closest_ids, closest_locations = bom.closest_first_bom(all_bom_sites_file, lat, lng, dates[0])

	# get climate from BOM
	closest_rain_i, closest_rain_dates, closest_rain_data = bom.closest_obs('136', dates, closest_names, closest_ids, closest_locations, zipped_sites_dir, bom.bom_obs_types)	
	closest_max_temp_i, closest_max_temp_dates, closest_max_temp_data = bom.closest_obs('123', dates, closest_names, closest_ids, closest_locations, zipped_sites_dir, bom.bom_obs_types)	
	closest_min_temp_i, closest_min_temp_dates, closest_min_temp_data = bom.closest_obs('122', dates, closest_names, closest_ids, closest_locations, zipped_sites_dir, bom.bom_obs_types)	

	# keep intersections
	multi_names = ["flows", "levels", "closest_min_temp", "closest_max_temp", "closest_rain"]
	multi_dates = [dates, level_dates, closest_min_temp_dates, closest_max_temp_dates, closest_rain_dates]
	multi_series = [flows, levels, closest_min_temp_data, closest_max_temp_data, closest_rain_data]
	intersection_i = utils.intersection_indices(multi_dates)
	for i in range(len(multi_dates)):
		multi_dates[i] = multi_dates[i][intersection_i[i]]
		multi_series[i] = multi_series[i][intersection_i[i]]

		assert numpy.all(multi_dates[i] == multi_dates[0])
		assert (multi_dates[i][-1] - multi_dates[i][0]).days == (len(multi_dates[i]) - 1) # check contiguous, TODO: otherwise add nans then interpolate

	print "SITE", lat, lng, dates[[0,-1]]
	print bom.bom_obs_types

	write_data = {
		"site_details": site_details, 
		"closest_details": {
			"closest_rain": { "name": closest_names[closest_rain_i], "id": closest_ids[closest_rain_i], "location": closest_locations[closest_rain_i], },
			"closest_max_temp": { "name": closest_names[closest_max_temp_i], "id": closest_ids[closest_max_temp_i], "location": closest_locations[closest_max_temp_i], },
			"closest_min_temp": { "name": closest_names[closest_min_temp_i], "id": closest_ids[closest_min_temp_i], "location": closest_locations[closest_min_temp_i], },
		},
		"dates" : [d.strftime("%d/%m/%Y %H:%M:%S") for d in multi_dates[0]],
	}
	for i in range(len(multi_dates)):
		write_data[multi_names[i]] = multi_series[i].tolist()

	with open(os.path.join("sw_data", site_id+'.json'), 'w') as f:
		f.write(json.dumps(write_data))


gauges = [
	"406207", # CAMPASPE RIVER @ EPPALOCK			#	or
	"406214", # enters # AXE CREEK @ LONGLEA			# then enters
	# Forrest Creek # enters 
	"406201", # CAMPASPE RIVER @ BARNADOWN			# but other creeks enter before then			# possibly 
	"406224", # enters # MOUNT PLEASANT CREEK @ RUNNYMEDE			# then 
	# "406275", # CAMPASPE RIVER @ BURNEWANG-BONN ROAD
	# "406218", # CAMPASPE RIVER @ CAMPASPE WEIR (HEAD GAUGE)
	"406202", # CAMPASPE RIVER @ ROCHESTER D/S WARANGA WESTERN CH SYPHN
	"406265", # CAMPASPE RIVER @ ECHUCA			# probably also relevant
]


def save_all():
	for site_id in gauges:
		save_site(site_id)


def load_sites():

	bulk_site_dir = "/home/mikey/Desktop/aus-hydro-data/downloaded_data/data.water.vic/download.20151022110838/"

	multi_dates = []
	multi_flows = []
	multi_levels = []

	for site_id in gauges:

		# get levels and flows from data.vic.water
		# site_id = "405230"
		data_types = ["MeanWaterLevel", "MeanWaterFlow"]
		site_details, data_types_values = vic_water_surface.read_bulk_downloaded_sw_file(bulk_site_dir, site_id, data_types)
		dates = data_types_values["MeanWaterFlow"]["dates"]
		flows = data_types_values["MeanWaterFlow"]["data"]
		level_dates = data_types_values["MeanWaterLevel"]["dates"]
		levels = data_types_values["MeanWaterLevel"]["data"]

		multi_dates.append(dates)
		multi_flows.append(flows)
		multi_levels.append(levels)


	flow_to_level


	# keep intersections
	intersection_i = utils.intersection_indices(multi_dates)
	for i in range(len(multi_dates)):
		multi_dates[i] = multi_dates[i][intersection_i[i]]
		multi_flows[i] = multi_flows[i][intersection_i[i]]

	for i in range(len(multi_dates)):
		plt.plot(multi_dates[i], multi_flows[i], label= gauges[i])
	plt.legend()
	plt.show()

if __name__ == '__main__':
	# save_all()

	load_sites()


