#WaterSuitability.py

import numpy as np
import pandas as pd


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

    def selectCoordinates(self, index_input, curve_option):
        """
        Select a set of xy coordinates (index_curve is a data imported from csv file, coded in core) for generating curve.
        To be used for uncertainty analysis through selecting different curves
        inputs: a curve csv file (for one species and one attribute), select one curve (column2-x) from that file
        outputs: coordinates.x, coordinates.y
        """

        #Create 2 column dataframe of Days and desired column
        temp_df = pd.DataFrame(index_input[curve_option], index=index_input["Days"])
        temp_df = temp_df.dropna()
        
        #Recreate Days column from index
        temp_df["x"] = temp_df.index
        
        temp_df.columns = ["x", "y"]
        
        return temp_df
        
        #coordinates['x']= index_input['x']
        #coordinates['y']= index_input['curve_option']
        #return coordinates

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
        
    def modifyCoordinates(self, coordinates,adjust):
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
    
    def WaterIndexWeightedAvg(self,flow_index, groundwater_index, groundwater_weight):
        """
        Calculate daily water index summary based on weighted average of daily flow index and groundwater index
        Output attributes:
        Date, water_index  
        """
        flow_index.merge(groundwater_index, left_index=True)
        
        water_index = flow_index * (1-groundwater_weight) + groundwater_index * groundwater_weight
        return water_index
