from integrated.Modules.Core.IntegratedModelComponent import Component
from integrated.Modules.Hydrology.Routing.Routing import Routing
from integrated.Modules.Hydrology.IHACRES.IHACRES import IHACRES
from integrated.Modules.Hydrology.Dam.Dam import Dam

import pandas as pd
import numpy as np

import time

class Hydrology(object):

    def __init__(self, combined_data, parameters=None):
            
        """
        parameters: Dict of IHACRES, Routing, Dam, Network parameters
        """

        self.Data = combined_data
        self.Climate = combined_data['climate']

        self.network = combined_data['network']

        # self.IHACRESparams  = combined_data['IHACRESparams']
        self.Routingparams  = combined_data["Routingparams"]

        self.Damparams      = combined_data['Damparams']

        self.climate_prep = time.time()
        self.prepClimateDataForNetwork()
        self.climate_prep = time.time() - self.climate_prep

        self.Routing = Routing(self.Climate, combined_data['water_volume'])
        self.IHACRES = IHACRES(self.Climate, combined_data['water_deficit'], combined_data['IHACRESparams'])

        self.Dam     = Dam(self.Climate, combined_data['dam_volume'])

        self.prep_time = 0.0
        self.calc_time = 0.0 
        self.dam = 0.0 
        self.route = 0.0 
        self.route_i = 0.0 
        self.inflow_time = 0.0
        self.ih = 0.0

    #End init()

    def prepClimateDataForNetwork(self):

        """
        Create a Dictionary of climate data for each node
        """

        network_data = self.network

        climate_data = self.Climate

        self.preppedClimate = {i: pd.DataFrame({'rainfall': climate_data["{node_id}_rain".format(node_id=ID)].values,
                                          'evap': climate_data["{node_id}_evap".format(node_id=ID)].values
                                          },
                                          index=climate_data['Date']
                    ) for i, ID in network_data['ID'].iteritems()}

        temp = self.network
        filler = np.zeros(len(temp['to node']))

        # filler200 = filler+200
        self.results_template = pd.DataFrame({
                'node_id': temp['node'],
                'calc_type': temp['type'].str.lower(), 
                'to_node': temp['to node'],
                #'a': temp['a'],
                #'b': temp['b'],
                #'h0': temp['h0'],
                'storage': filler.copy(), #Fill storage column with 0's to begin with
                'level': filler.copy(), #Fill storage column with 0's to begin with
                'RRstorage': filler.copy(), #Fill prev column with 0's to begin with
                'deficit': filler.copy()+200, #Fill deficit column with 0's to begin with
                'flow': filler.copy() #Fill flow column with 0's to begin with
                
        }, index=temp['node']) #.sort_values('to_node')

    #End prepClimateDataForNetwork)

    def run(self, this_time, last_time, data=None):

        """
        :param this_time: current timestep as string
        """

        # if len(data) == 0:
        #     data = {}
        #     # data[this_time] = {}
        #     data[last_time] = self.results_template.copy()
        try:
            last = data[last_time]
        except KeyError:
            data[last_time] = self.results_template.copy()
            last = data[last_time]
        except TypeError:
            data = {}
            data[last_time] = self.results_template.copy()
            last = data[last_time]

        data[this_time] = self.results_template.copy()
        
        #For each row in results dataframe (denoted by axis=1), apply the calcFlow method
        #x represents a given row
        #So we are calling calcFlow() with the current row, the complete dataframe, and this timestep
        climate_data = self.preppedClimate
        data[this_time] = data[last_time].apply(self.calcFlow, args=(last, this_time, climate_data, ), axis=1)

        # for i, row in data[last_time].iterrows():
        #     data[this_time].loc[i] = self.calcFlow(row, last, this_time, climate_data)
        # #End for

        return data

    #End run()

    def calcFlow(self, node, df, this_time, timestep_climate):

            # if time.strptime(this_time, "%d/%m/%Y") == time.strptime("04/09/1900", "%d/%m/%Y"):

            #     print node
            #     print df
            #     print this_time
            #     print timestep_climate

            #     import sys; sys.exit()

            prep_time = time.time()

            #get the previous values for this node
            prev_RRstorage, calc_type, prev_CMD, flow, level, node_id, prev_storage, to_node = node

            timestep_climate = timestep_climate[node_id].loc[this_time].values

            self.prep_time += time.time() - prep_time

            ct = time.time()
            node['flow']=0.0
            node_inflow=0.0

            if (calc_type == 'ihacres') or (calc_type == 'routing') or (calc_type == 'end'):

                # print "Calling IHACRES"
                ih = time.time()

                #node['deficit'], node['flow'], node['RRstorage'] = self.IHACRES.calcCMD(node_id, timestep_climate, prev_CMD, prev_RRstorage, self.IHACRESparams)
                node['deficit'], flow, node['RRstorage'] = self.IHACRES.calcCMD(node_id, timestep_climate, prev_CMD, prev_RRstorage)
                node['flow'] = node['flow'] + flow

                self.ih += time.time() - ih
            #End common check

            if (calc_type == 'ihacres') or (calc_type == 'end'):
                
                # print(node['node_id'],node['flow'],node['storage'],node['RRstorage'],node['deficit'])
                self.calc_time += time.time() - ct
                return node

            else:

                inflow_time = time.time()
                node_inflow = df.loc[df['to_node'] == node_id, 'flow'].sum()

                irrig_ext=0; base_flow=0.0; deep_drainage=0; storage_coef=0.5; ET_f=0.8*10*0.01

                self.inflow_time = time.time() - inflow_time

                if calc_type == 'routing':

                    # run Routing module
                    rt = time.time()
                    
                    #timing routing prep
                    route_prep = time.time()

                    b_id, n_id, storage_coef, ET_f, area = self.Routingparams.loc[self.Routingparams.index == node_id].iloc[0]
                    route_params = [storage_coef, ET_f, area]

                    local_inflow = flow

                    self.route_i += time.time() - route_prep

                    flow, node['storage'] = self.Routing.calcFlow(node_id, timestep_climate, node_inflow, irrig_ext, local_inflow, base_flow, deep_drainage, route_params)

                    # if time.strptime(this_time, "%d/%m/%Y") == time.strptime("01/09/1900", "%d/%m/%Y"):
                    #     print flow
                    #     print node
                    #     import sys; sys.exit()

                    # node['flow'] = node['flow'] + flow

                    self.route += time.time() - rt

                elif calc_type == 'dam':

                    dt = time.time()

                    g_id, n_id, storage_coef, area, max_storage = self.Damparams.loc[self.Damparams.index == node_id].iloc[0]
                    dam_params = [storage_coef, area, max_storage]
                    
                    flow, node['storage'] = self.Dam.calcFlow(node_id, timestep_climate, node_inflow, irrig_ext, base_flow, deep_drainage, dam_params)

                    # node['flow'] = node['flow'] + flow

                    self.dam += time.time() - dt

                else:
                    print "No method defined"
                    import sys
                    sys.exit(1)
                #End if                

            #End calc_type check

            node['flow'] = node['flow']+flow

            #Grab vars to calculate level with
            g_id, n_id, to_node, calc_type, a, b, h0 = self.network.loc[self.network.index == node_id].iloc[0]

            # a=1/1000.; b=1.7; h0=100.
            node['level'] = a*np.power(node['flow'],b)+h0
            # print(level)
            # node['storage'] = level

            # print(node['node_id'],node['flow'],node['storage'],node['RRstorage'],node['deficit'])

            self.calc_time += time.time() - ct

            return node

    def overflow(self):
            pass

    def release(self):
            pass

    def infiltration(self):
            pass

    def calcStorage(self):
            pass
