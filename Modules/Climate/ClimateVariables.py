from integrated.Modules.Core.IntegratedModelComponent import Component

import pandas as pd

class Climate(Component):

    """
    Serves as an interface to climate data
    """

    def __init__(self, **kwargs):

        #Set all key word arguments as attributes
        for key, value in kwargs.items():
            setattr(self, key, value)
        #End For
    #End init()

    def getSummerRainfall(self, timestep, data=None):

        """
        Modified French-Schultz approach as in Oliver et al. (2008)

        Stored soil water can be assumed to be 25-30 percent of summer rainfall (defined as December and April).
        This assumed to be 0 in original French-Schultz (Oliver et al. 2008)

        For the given timestep, get previous climate season's rainfall

        :param timestep: 
        :param data: Climate data

        """

        year = timestep.year

        if data is None:
            data = self.data
        #End if

        start_date = '{y}-12-01'.format(y=year-1)
        end_date = '{y}-04-30'.format(y=year)

        mask = (data.index >= start_date) & (data.index <= end_date)

        return data.loc[mask]

#End ClimateVariables
