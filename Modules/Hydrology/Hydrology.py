import pandas as pd
from integrated.Modules.Core.IntegratedModelComponent import Component
from integrated.Modules.Hydrology.Routing.Routing import Routing

import numpy as np

class Hydrology(object):

	def __init__(self, combined_data, parameters=None):
		

		"""
		parameters: Dict of IHACRES, Routing, Dam, Network parameters
		"""

		self.Data = combined_data
		self.Climate = combined_data['climate']
		self.network = combined_data['network']

		self.parameters = parameters

		self.prepClimateDataForNetwork()

		self.Routing = Routing(self.Climate, combined_data['water_volume'])

		# parameters = {
		# 	"IHACRES": None,
		# 	"Routing": None,
		# 	"Dam": None,
		# 	"Network": None
		# }

	#End init()

	def prepClimateDataForNetwork(self):

		"""
		Create a Dictionary of climate data for each node
		"""

		climate = {}
		network_data = self.network

		climate_data = self.Climate

		for ID in network_data['ID']:

			node_id = network_data[network_data['ID'] == ID]['node'].iloc[0]
			climate[node_id] = pd.DataFrame()
			climate[node_id]['rainfall'] =climate_data["{ID}_rain".format(ID=ID)]
			climate[node_id]['evap'] = climate_data["{ID}_evap".format(ID=ID)]
			climate[node_id].index = climate_data['Date']
		#End for

		self.preppedClimate = climate

	#End prepClimateDataForNetwork)

	def run(self, this_time, data=None):

		"""
		:param prev_water_store: Water volume from previous timestep
		"""

		if data is None:
			data = {
				'node_id': self.network['node'],
				'calc_type': self.network['type'], 
				'to_node': self.network['to node'], 
				'storage': np.zeros(len(self.network['to node'])), #Fill storage column with 0's to begin with
				'prev_storage': np.zeros(len(self.network['to node'])) #Fill prev column with 0's to begin with
			}

			results = pd.DataFrame(data)
		else:
			results = data
		
		#For each row in results dataframe (denoted by axis=1), apply the calcFlow method
		#x represents a given row
		#So we are calling calcFlow() with the current row, the complete dataframe, and this timestep
		results = results.apply(lambda x: self.calcFlow(x, results, this_time), axis=1)

		return results
	#End run()

	def calcFlow(self, node, df, this_time):

		node_id = node['node_id']
		climate_for_node = self.preppedClimate[node_id]

		#Get climate data for this timestep
		timestep_climate = climate_for_node[climate_for_node.index == str(this_time.strftime('%d/%m/%Y'))]

		#Get the calculation type (routing, IHACRES, etc.)
		calc_type = str(node['calc_type']).lower()

		#Sum all the inflows for this node
		node_inflow = df[df['to_node'] == node_id]['storage'].sum()

		#get the previous storage for this node
		prev_storage = df[df['node_id'] == node_id]['prev_storage'].iloc[0]

		if calc_type == 'routing':

			#calcFlow(node_id, climate, prev_storage, inflow, irrig_ext, local_inflow, base_flow, deep_drainage, storage_coef, ET_f)
			node['storage'] = self.Routing.calcFlow(node_id, timestep_climate, prev_storage, node_inflow, 0, 0, 5, 0, 0.5, 0.8)

		elif calc_type == 'ihacres':
			# print "Calling IHACRES"
			pass
		elif calc_type == 'dam':
			# print "Calculation for Dam"
			pass
		else:
			print "No method defined"

		return node

	def overflow(self):
		pass

	def release(self):
		pass

	def infiltration(self):
		pass

	def calcStorage(self):
		pass
