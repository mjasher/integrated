#Management
from __future__ import division
from integrated.Modules.Core.IntegratedModelComponent import Component
from integrated.Modules.Farm.Management.Manager import FarmManager
from integrated.Modules.Farm.Fields.Field import FarmField
from integrated.Modules.Farm.Fields.Soil import SoilType
from integrated.Modules.Farm.Irrigations.IrrigationPractice import IrrigationPractice

#Linear programming
from scipy.optimize import linprog as lp

#remove this when ready
from random import randint

import pandas as pd
import numpy as np

class PlasticManager(FarmManager):

    """
    Plastic Farm Manager - Highly opportunistic management style

    # .. inheritance-diagram:: integrated.Modules.Farm.Farms.Management.FarmManager
    #    :parts: 2

    """

    def __init__(self, Farm, water_sources, storages, irrigations, crops):

        """
        :param Farm: Farm Object representing the Farm to manage
        """

        #Call parent constructor
        FarmManager.__init__(self, Farm, water_sources, storages, irrigations, crops)
        #Python 3 version of the above
        #super().__init__(Farm, water_sources, irrigations, crops)

        self.crop_rotation_counter = {}

    #End __init__()

    def getAvailableCropChoices(self):
        crop_choices = {}
        for Field in self.Farm.fields:
            crop_choices[Field.name] = self.getNextCropInRotation(Field)
        #End for
        
        return crop_choices
    #End getAvailableCropChoices()

    def getNextCropInRotation(self, Field):

        """
        Flexible Crop Rotation
        If current rotation has finished, get all possible crops that is not the current one    

        :param Field: FarmField object
        
        :returns: (list) Current or all available crop objects
        
        """

        crops = self.crops

        #crop_rotation = self.crop_rotations

        Crop = Field.Crop

        if Crop == None:
            available_crops = crops[:]
        else:

            self.crop_rotation_counter[Crop.name] = self.crop_rotation_counter.get(Crop.name, 0)

            if self.crop_rotation_counter[Crop.name] < Crop.rotation_length:
                self.crop_rotation_counter[Crop.name] += 1
                available_crops = [Crop.getCopy()]
            else:
                available_crops = [c.getCopy() for c in self.crop_rotations if c.name != Crop.name]

                #Reset counter for current crop
                self.crop_rotation_counter[Crop.name] = 0
            #End if
        #End if

        return available_crops

    #End getNextCropInRotation()

#End FarmManagement()