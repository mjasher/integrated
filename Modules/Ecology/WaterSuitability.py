#WaterSuitability.py

import numpy as np
import pandas as pd


class WaterSuitability: 
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
    
    def selectCoordinates(self,curve_option):
        """
        Select a set of xy coordinates (imported from csv file) for generating curve.
        To be used for uncertainty analysis through selecting different curves
        """
        return coordinates

    def selectWeights(self,weight_option):
        """
        Select a set of weight (imported from csv file) for aggregating indexes.
        To be used for uncertainty analysis through selecting different weights
        """
        return weights            
        
    def modifyCoordinates(self, coordinates):
        """
        Adjust the predefined xy coordinates e.g. +_ 10%
        To be used for uncertainty analysis through allowing the predefined xy coordinates to move around
        """
        return new_coordinates
    

     def makeIndexCurve(self, coordinates):
         """
         Create an index curve based on xy coordinates. 
         The two ends of the curve extend flat (i.e. the same as the first/last y value)
         """        
         return index_curve
    
    def WaterIndexWeightedAvg(self,flow_index, groundwater_index):
        """
        Calculate daily water index summary based on weighted average of daily flow index and groundwater index
        Output attributes:
        Date, water_index
        """
        return water_index
