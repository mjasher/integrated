#WaterSuitability.py

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d


class WaterSuitability(object):
    """
    Model water suitability index for vegetation based on flow and groundwater. 
    The index was identified based on expert knowledge in vegetation water requirements
    """

    def __init__(self, **kwargs):

        """
        species: species (e.g. river red gum) and stage (e.g. maintenance vs regeneration)
        eco_site: ecological model site
        """

        self.species = kwargs.pop('species', 'RRGMS')
        self.eco_site = kwargs.pop('eco_site','1')        

        
    #End init()

    def getAssetParam(self, asset_table, gauge, col):
        return asset_table[asset_table["Gauge"] == int(gauge)][col].iloc[0]
    #End getAssetParam()


    def selectCoordinates(self, index_input, cols):
        """
        Select a set of xy coordinates (index_curve is a data imported from csv file, coded in core) for generating curve.
        To be used for uncertainty analysis through selecting different curves

        :param index_input: Pandas Dataframe of possible x and y coordinates, where x is the index.
        :param cols: List of column names for x and y coordinates

        :returns: Two column Pandas Dataframe of x and y

        """

        #TODO
        #Create n column dataframe of x and desired column(s)

        temp_df = pd.DataFrame(dict(x=index_input.index, y=index_input[cols]))
        temp_df = temp_df.dropna()
        
        return temp_df
        
    #End selectCoordinates()

    def selectWeights(self, weight_input, weight_option):
        """
        Select a set of weight (imported from csv file) for aggregating indexes.
        To be used for uncertainty analysis through selecting different weights
        outputs: duration_weights, timing_weights, dry_weights
        """
        
        weights = {}
        weights['duration'] = weight_input[weight_input['Attribute'] == 'Duration'][weight_option]
        weights['timing'] = weight_input[weight_input['Attribute'] == 'Timing'][weight_option]
        weights['dry'] = weight_input[weight_input['Attribute'] == 'Dry'][weight_option]
        return weights            
    
    #End selectWeights()

    def selectWeightForSpecies(self, weights, species_name, weight_name=None):

        if weight_name is not None:
            df = weights.loc[weights.index == species_name, weight_name]
        else:
            #Return all weights if none specified
            df = weights.loc[weights.index == species_name]
            
        #End if

        return df
    #End selectWeightForSpecies
        

    def modifyCoordinates(self, coordinates, adjust):
        """
        Adjust the predefined xy coordinates e.g. +_ 10%
        To be used for uncertainty analysis through allowing the predefined xy coordinates to move around
        """
        new_coordinates['x']= coordinates['x']*adjust
        new_coordiantes['y']= coordinates['y']*adjust
        return new_coordinates


#    def makeIndexCurve(self, coordinates):
#        """
#        Create an index curve based on xy coordinates. 
#        The two ends of the curve extend flat (i.e. the same as the first/last y value)
#        """
#        return index_curve
    
    def waterIndexWeightedAvg(self, flow_index, groundwater_index, groundwater_weight):
        """
        Calculate daily water index summary based on weighted average of daily flow index and groundwater index

        Output attributes:
        Date, water_index  
        """

        flow_index.merge(groundwater_index, left_index=True)
        
        water_index = flow_index * (1-groundwater_weight) + (groundwater_index * groundwater_weight)
        return water_index

    def calcWaterSuitabilityIndex(self, gw_data, sw_data, gw_weight, sw_weight):

        """
        :math:`I = w_{g}G + w_{s}S`

        where 

        * :math:`I` denotes the water suitability index

        * :math:`G` is the groundwater suitability index

        * :math:`S` is the surface water suitability index

        * :math:`w_{g}` weight for groundwater index

        * :math:`w_{s}` weight for surface water index

        Here groundwater data is daily data and surface water data reflects grouped flooding events. \\\
        Because of this, the surface water index is NaN for datetime with no observations. \\\
        To account for this, we fill these NAs with the weighted GW index as SW Index is 0 in those circumstances

        :param gw_index: groundwater index
        :param sw_index: surface water index
        :param gw_weight: groundwater index weight
        :param sw_weight: surface water index weight
        :returns: water suitability index
        :return type: Pandas Series

        """

        # import time
        # start = time.time()
        # print "Took {s} seconds".format(s = time.time() - start)

        #Fill column with GW datatime. Use this to search the SW dataframe
        temp = gw_data.index.astype(str)
        # gw_data['sw_index'] = temp.tolist()

        #Get the start and end dates to search between
        timeframe = pd.DataFrame(dict(start=pd.to_datetime(sw_data['start']), end=pd.to_datetime(sw_data['end']), sw_suit_index=sw_data['sw_suitability_index']))
        

        #Create dataframe to house the suitability indexes
        series = pd.DataFrame(dict(datetime=temp, gw_suit_index=gw_data['gw_suitability_index'], sw_suit_index=np.zeros(len(gw_data['gw_suitability_index'])) ))


        for i, row in timeframe.iterrows():
            series.loc[row['start']:row['end'], 'sw_suit_index'] = row['sw_suit_index']
        #End for

        gw_data['sw_suitability_index'] = series['sw_suit_index']
        gw_data['water_suitability_index'] = ((gw_weight*gw_data['gw_suitability_index']) + (sw_weight*gw_data['sw_suitability_index']))

        gw_data[gw_data[['sw_suitability_index']] == 0] = np.nan

        return gw_data

    #End calcWaterSuitabilityIndex()


    def calcGWSuitabilityIndex(self, gw_index, S_index):

        """

        :math:`G = L(d) * E(S)`

        where
        * :math:`G` is groundwater suitability index

        * :math:`L` is a function of groundwater depth which produces an index

        * :math:`d` is groundwater depth

        * :math:`E` is a function of salinity which produces a salinity index

        * :math:`S` is salinity

        :returns: groundwater suitability index
        :return type: numeric (?)
        """

        return gw_index * S_index

    #End calcGWSuitabilityIndex()

    def calcSWSuitabilityIndex(self, fd, ft, dp):

        """

        Currently a stub. Implementing child classes should (re)define this method

        All dicts should consist of the weight and index for a given species

        :math:`S = w_{d}D(f_{d}) + w_{t}T(f_{t}) + w_{f}F(f_{dp})`

        where

        * :math:`S` is surface water suitability index

        * :math:`w_{d}` weight for flood duration

        * :math:`D` is a function of flood duration which produces a flood duration index

        * :math:`f_{d}` flood duration

        * :math:`w_{t}` weight for flood timing

        * :math:`T` is a function of flood timing which produces a flood timing index

        * :math:`f_{t}` flood timing

        * :math:`w_{f}` weight for inter-flood dry period

        * :math:`F` is a function of inter-flood dry period which produces a dry period index

        * :math:`f_{dp}` inter-flood dry period

        :param fd: Dict of flood duration parameters
        :param ft: Dict of flood timing parameters
        :param dp: Dict of flood dry period parameters

        :returns: surface water suitability index
        :return type: time series (?)

        """

        pass

    #End calcSWSuitability

    def calcSalinityIndex(self):
        pass

