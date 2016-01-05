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

    .. inheritance-diagram:: integrated.Modules.Farm.Farms.Management.FarmManager
       :parts: 2

    """

    def __init__(self, Farm, water_sources, irrigations, crops):

        """
        :param Farm: Farm Object representing the Farm to manage
        """

        #Call parent constructor
        FarmManager.__init__(self, Farm, water_sources, irrigations, crops)
        #Python 3 version of the above
        #super().__init__(Farm, water_sources, irrigations, crops)

    #End __init__()

#End FarmManagement()