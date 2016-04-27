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

    def getSummerRainfall(self, timestep, data=None, summer_months=[1, 4]):

        """
        Modified French-Schultz approach as in Oliver et al. (2008; 2009)

        Stored soil water can be assumed to be 25-30 percent of summer rainfall (defined as January and April).
        This assumed to be 0 in original French-Schultz (Oliver et al. 2008)

        For the given timestep, get previous climate season's rainfall

        :param timestep: 
        :param data: Climate data
        :param summer_months: List of start and end month (inclusive) where 1 = Jan, 2 = Feb, ... 12 = Dec.

        """

        year = timestep.year

        if data is None:
            data = self.data
        #End if

        start = summer_months[0]
        end = summer_months[1]

        if start > end:
            start_date = '{y}-{m}-01'.format(y=year-1, m=start)
        else:
            start_date = '{y}-{m}-01'.format(y=year, m=start)
        #End if

        #Move to actual last day of month
        end_date = '{y}-{m}-15'.format(y=year, m=end)
        end_date = pd.Timestamp(end_date) + pd.offsets.MonthEnd(1)

        return self.getSeasonRange(start_date, end_date, data)
    #End getSummerRainfall()

    def getSeasonalRainfall(self, season_range, data=None):

        """
        Retrieve seasonal rainfall

        :param season_range: List-like, start and end dates, can be string or datetime object
        :param data: Pandas Series to slice

        :returns: numeric of seasonal rainfall
        """

        if data is None:
            data = self.data
        #End if

        start = season_range[0]
        end = season_range[1]

        assert end > start, 'Season end date cannot be earlier than start date ({} < {} ?)'.format(start, end)

        return self.getSeasonRange(start, end, data).cumsum().iloc[-1, 0]

    #End getSeasonalRainfall()

    def getSeasonRange(self, start, end, data):

        mask = (data.index >= start) & (data.index <= end)

        return data.loc[mask]

#End ClimateVariables
