from integrated.Modules.Core.IntegratedModelComponent import Component

import pandas as pd

class Climate(Component):

    """
    Serves as an interface to climate data
    """

    def __init__(self, data, **kwargs):

        self.data = data

        #Set all key word arguments as attributes
        for key, value in kwargs.items():
            setattr(self, key, value)
        #End For

        climate_year = self.data.groupby(by=self.data.index.year).sum()

        self.description = climate_year.describe()
        self.description.loc['90%', :] = climate_year.quantile(q=0.9)

        self.min_rainfall = self.description.loc['min', 'rainfall']
        self.max_rainfall = self.description.loc['max', 'rainfall']
        self.med_rainfall = self.description.loc['50%', 'rainfall'] #Median rainfall
        self.mean_rainfall = self.description.loc['mean', 'rainfall']
        self.high_rainfall = self.description.loc['90%', 'rainfall']

    #End init()

    def getClimateAttrib(self, attrib, phenom='rainfall'):
        """
        Retrieve climate attribute
        e.g. standard deviation of rainfall
            return self.data.groupby(by=self.data.index.year).sum().describe().loc['std', :]

        :param attrib: Climate attribute accessible through a Pandas Dataframe describe() or 90th percentile
        :param phenom: Desired climate phenomenon, e.g. Rainfall or Evapotranspiration
        """
        return self.description.loc[attrib, phenom]
    #End getClimateAttrib()

    def getAnnualRainfall(self, timestep, data=None):
        """
        Calculate the total amount of rainfall that occured in a year, given in the timestep

        :param timestep: (Datetime object or int) that contains a year
        """

        year = timestep if type(timestep) == int else timestep.year

        data = self.data if data == None else data

        year_data = data[data.index.year == year]

        yearly_rainfall = year_data.sum()

        return yearly_rainfall['rainfall']
    #End getAnnualRainfall()
    
    def getSummerRainfall(self, timestep, data=None, summer_months=[1, 4]):

        """
        Modified French-Schultz approach as in Oliver et al. (2008; 2009)

        Stored soil water can be assumed to be 25-30 percent of summer rainfall (defined as January to April).
        This assumed to be 0 in original French-Schultz (Oliver et al. 2008)

        For the given timestep, get previous climate season's rainfall

        :param timestep: 
        :param data: Climate data
        :param summer_months: List of start and end month (inclusive) where 1 = Jan, 2 = Feb, ... 12 = Dec.

        """

        if data is None:
            data = self.data
        #End if

        return self.getInterYearRange(timestep, summer_months, days=[1, None], data=data)

    #End getSummerRainfall()

    def getInterYearRange(self, timestep, months, days=[1, 15], data=None):

        """
        Returns data range for a given inter-year timeframe, e.g. August (of current year) - May (of next year)
        
        :param timestep: Current timestep to consider
        :param months: Tuple of Start and end month
        :param days: int of start/end day or None. If end day is None, moves to last day of given month
        :param data: Pandas dataframe of data to extract
        """

        if data is None:
            data = self.data
        #End if

        move_end_day = False
        if days[1] == None:
            move_end_day = True
            days[1] = 15
        #End if

        start_date, end_date = self._adjustInterYearDates(timestep, months, days)

        if move_end_day == True:
            end_date = self._moveToEndOfMonth(end_date)
        #End if

        return self.getSeasonRange(start_date, end_date, data)
    #End getInterYearRange()

    def _moveToEndOfMonth(self, dt):
        """
        Move day of given datetime to the last day of that month

        :param dt: (string) Datetime to adjust
        """
        return pd.Timestamp(dt) + pd.offsets.MonthEnd(1)
    #End _moveToEndOfMonth()

    def _adjustInterYearDates(self, dt, months, days=[15,15]):

        """
        Given a timestamp and months that may (or may not) be inter-year (e.g. Jan-Feb or August-May)
        determine what the start and end date would be for the given range
        """

        start, end = months
        s_day, e_day = days

        ts_month = dt.month

        if start > end:
            if ts_month >= start:
                start_date = '{y}-{m}-{d}'.format(y=dt.year, m=start, d=s_day)
                end_date = '{y}-{m}-{d}'.format(y=dt.year+1, m=end, d=e_day)
            else:
                start_date = '{y}-{m}-{d}'.format(y=dt.year-1, m=start, d=s_day)
                end_date = '{y}-{m}-{d}'.format(y=dt.year, m=end, d=e_day)
            #End if
        else:
            start_date = '{y}-{m}-{d}'.format(y=dt.year, m=start, d=s_day)
            end_date = '{y}-{m}-{d}'.format(y=dt.year, m=end, d=e_day)

        return start_date, end_date
    #End _adjustInterYearDates()

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

        start, end = season_range

        if type(start) == str:
            start = pd.to_datetime(start)
        #End if

        if type(end) == str:
            end = pd.to_datetime(end)
        #End if

        assert end > start, 'Season end date cannot be earlier than start date ({} < {} ?)'.format(start, end)

        return self.getSeasonRange(start, end, data).cumsum().iloc[-1, 0]

    #End getSeasonalRainfall()

    def getSeasonRange(self, start, end, data):

        mask = (data.index >= start) & (data.index <= end)

        return data.loc[mask]

    #End getSeasonRange()

    def inIrrigationSeason(self, timestep, months=[8, 5], days=[15, 15], data=None):

        """
        Checks to see if given timestep is in an irrigation season
        TODO: Think of better place for this, not really climate related
        """

        if data is None:
            data = self.data
        #End if

        irrigation_season = self.getInterYearRange(timestep, months, days, data=data)

        return (timestep in irrigation_season.index)

    #End inIrrigationSeason()

#End ClimateVariables
