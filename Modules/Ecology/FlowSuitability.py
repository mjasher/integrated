# FlowSuitability.py

from WaterSuitability import WaterSuitability

import pandas as pd
import numpy as np

class FlowSuitability(WaterSuitability):

    def __init__(self, asset_table, species_list, indexes, weights):
        """
        :param asset_table: Pandas dataframe of asset information
        :param species_list: list of species names 
        :param indexes: indexes for the given list of species
        """

        self.asset_table = asset_table
        self.species_list = species_list
        self.indexes = indexes
        self.weights = weights

        #Load in indexes for species
        # for i, species in enumerate(species_list):

    #End init()

    def rollingCounter(self, val):

        """
        Function to apply when counting sequential event days
        """

        val = pd.Timedelta(val)

        if val == pd.Timedelta(days=1) or val <= pd.Timedelta(days=self.min_sep):
            self.rolling_count += 1
        else:
            self.rolling_count = 1

        return self.rolling_count
    #End rollingCounter()

    #Group events together by id then remove events that do not fit the min duration rule
    def grouper(self, start, end):

        if start == True:
            return self.grouper_id
        
        if end == True:
            self.grouper_id += 1
            return self.grouper_id - 1
        else:
            return self.grouper_id
    #End grouper

        
    def floodEvents(self, flow_df, threshold=4000, min_duration=3, min_separation=2):
        
        """
        Determine flow events based on daily flow, like R hydromad eventseq()

        :param flow_df: Pandas dataframe of daily flow in ML/Day
        :param threshold: Flood event threshold; flow must be higher than this to be classified as a flooding event.
        :param min_duration: Minimum number of days that defines a flooding event
        :param min_separation: Minimum number of days separating events. If fewer, assume it is a fluctuation in the current event.

        :Returns: Pandas DataFrame of flood events
            start: event start date
            end: event end date
            duration: Duration of event
            dry_period: Preceeding dry period
            timing: 1-12, representing month of event start (1 = Jan, 12 = December)
        """

        events = pd.DataFrame(data=flow_df, index=flow_df.index)
        # col = temp_df.columns[0]

        events['datetime'] = events.index

        #If value is above threshold and the time distance between flow observation is >= min_separation, 
        #and the flow time is >= min_duration, count as event
        events = events[events.Flow >= threshold]

        # events.loc[:, 'dry_period'] = events['datetime'].diff()
        events['dry_period'] = events['datetime'].diff()

        #Static variable for local function
        self.rolling_count = 1
        self.min_sep = min_separation

        events.loc[:, 'counter'] = events['dry_period'].apply(self.rollingCounter)
        
        #Select all the rows that have a duration of 1, and the next row is also a duration of 1
        #These will be the start of an event
        events.loc[:, 'starts'] = events['counter'].diff() <= 0
        events.loc[:, 'ends'] = events['counter'].diff(-1) > -1

        self.grouper_id = 1

        events.loc[:, 'group'] = events[['starts', 'ends']].apply(lambda x: self.grouper(*x), axis=1)

        #Remove groups below the min duration rule
        group = events.groupby('group')['Flow'].count() < min_duration

        #Remove the groups found to be below the min duration rule
        events = events[~events["group"].isin(group[group == True].index)]

        events['duration'] = events[events['ends'] == True]['counter']

        group = events.groupby(['group'], sort=False)

        temp = group['dry_period'].max()

        flow_events = pd.DataFrame()
        flow_events['start'] = group['datetime'].min()
        flow_events['end'] = group['datetime'].max()
        flow_events['duration'] = group['duration'].max()
        flow_events['dry_period'] = temp.astype('timedelta64[ns]').apply(lambda x: int(x / np.timedelta64(1, 'D'))) #Convert to integer of days
        flow_events['timing'] = flow_events['start'].map(lambda x: x.to_datetime().month) 

        return flow_events

    #End floodEvents()
    
    def floodIndexes(self, flood_events_df, coordinates):
        """
        Calculate index for each flood attribute based on index curve (defined in WaterSuitability.py)
        input: coordinates is a dict of duration, timing, dry coordinates
        Output attributes:
        event id, start date, end date, duration, startmonth (month when the event start), dry (interflood dry period),duration index, timing index, interflood dry period index
        """

        # df = pd.DataFrame()
        for attribute, coords in coordinates.iteritems():

            try:
                flood_events_df['flood_{a}'.format(a=attribute)] = self.calcIndex(flood_events_df[attribute], coords)
            except KeyError:
                #Missing attribute in flood events
                pass
            
        #End for

        return flood_events_df
        
    #End floodIndexes()

    def gwIndexes(self, data, coordinates):

        """
        Calculate index for groundwater and add to the given primary DataFrame

        :param data: Pandas DataFrame of groundwater level observations
        :param coordinates: DataFrame of x, y coords
        """

        return self.calcIndex(data, coordinates)

    #End gwIndexes


    def calcIndex(self, data, coords):

        return np.interp(data, coords.x, coords.y)

        # try:
        #     x = np.interp(data, coords.x, coords.y)
        #     return x
        # except TypeError:
        #     print data
        #     print coords.x
        #     print coords.y
        #     print "Error occured here!"
        #     import sys
        #     sys.exit()

    #End calcIndex()

    def flowSummary(self, df, func_name):

        """
        Calculate summary statistics (defined by function).

        :param df: Pandas dataframe, must have datetime index
        :param func_name: statistical attribute as found in Python pandas: min, max, median, etc.

        """

        grouping = df.groupby(df.index.year)
        
        func = getattr(grouping, func_name)
        return func()

    #End flowSummary()
    
    def generateEnvIndex(self, asset_id, scen_data, salinity=10000, **kwargs):

        """
        Generate environmental indexes for the given list of species

        :param asset_id: Column position in dataframe, zero-based index
        :param scen_data: scenario data in a Pandas dataframe
        :param ecospecies: name of species
        :param salinity: Default salinity value to use if no data found. Assumes 10,000ppm
        """

        ecospecies = self.species_list

        asset_table = self.asset_table

        gauge = str(asset_table["Gauge"][asset_id])

        surfaceflow = scen_data[gauge]["Flow"]
        baseflow = scen_data[gauge]["Baseflow"]

        #Get GW level data with datetime
        gw_data = scen_data["gwlevel"][["A{a}".format(a=asset_id+1)]].dropna()

        try:
            #TODO: Refactor this to reflect format of data files
            #If using data, number of observations has to equal GW data
            salinity_data = scen_data["salinity"]
        except KeyError:
            #Use default value
            salinity_data = salinity

        gw_mean = self.flowSummary(gw_data, "mean")
        baseflow_median = self.flowSummary(gw_data, "median")
        num_days_flow_ceased = self.ceaseDays(surfaceflow)
        total_flow = self.flowSummary(surfaceflow, "sum")

        min_gap = self.getAssetParam(asset_table, gauge, 'Event_gap')
        min_size = self.getAssetParam(asset_table, gauge, 'Event_dur')

        flow_events = self.floodEvents(surfaceflow, \
            threshold=self.getAssetParam(asset_table, gauge, 'Event_threshold'), \
            min_separation=min_gap, \
            min_duration=min_size )

        event_info = self.eventInfo(flow_events)
        weights = self.weights

        #Generate indices for each species
        results = {}

        for i, species in enumerate(ecospecies):

            #Create Dict entry for species
            results[species] = {}

            timing_coords = self.selectCoordinates(self.indexes["{s}_timing".format(s=species)], cols=["Month", "Index"])
            duration_coords = self.selectCoordinates(self.indexes["{s}_duration".format(s=species)], cols=["Days", "Index"])
            dry_coords = self.selectCoordinates(self.indexes["{s}_dry".format(s=species)], cols=["Days", "Index"])
            gw_level_coords = self.selectCoordinates(self.indexes["{s}_gwlevel".format(s=species)], cols=["Level_m", "Index"])
            salinity_coords = self.selectCoordinates(self.indexes["{s}_salinity".format(s=species)], cols=["ppm", "Index"])

            coords = {
                "timing": timing_coords,
                "duration": duration_coords,
                "dry_period": dry_coords,
            }

            flow_events = self.floodIndexes(flow_events, coords)
            species_weights = self.selectWeightForSpecies(weights, species)

            temp_gw_data = gw_data.copy()

            temp_gw_data['gw_index'] = self.gwIndexes(temp_gw_data, gw_level_coords)

            #Assume 10,000 ppm, could be replaced with daily data
            temp_gw_data['salinity'] = temp_gw_data['gw_index'] * salinity_data

            temp_gw_data['salinity_index'] = self.calcIndex(temp_gw_data['salinity'], salinity_coords)

            # weight_for_species = self.weights.loc[species]
            flow_events['sw_suitability_index'] = self.calcSWSuitabilityIndex(flow_events, species_weights)

            temp_gw_data['gw_suitability_index'] = self.calcGWSuitabilityIndex(temp_gw_data['gw_index'], temp_gw_data['salinity_index'])

            #Adds SW suitability and Water suitability indexes to GW dataframe
            temp_gw_data = self.calcWaterSuitabilityIndex(temp_gw_data, flow_events, gw_weight=1, sw_weight=1)

            # print flow_events[['start', 'end', 'sw_suitability_index']].head()
            # print flow_events.head()
            # print temp_gw_data.head(25)
            
            results[species]['sw'] = flow_events
            results[species]['gw'] = temp_gw_data
            results[species]['water_index'] = temp_gw_data['water_suitability_index']

        #End for

        return results

    #End generateEnvIndex()

    def eventInfo(self, flood_event):
        
        timing = flood_event['timing']
        duration = flood_event['duration']
        dry_period = flood_event['dry_period']

        return pd.DataFrame(dict(timing=timing, duration=duration, dry_period=dry_period))

    #End eventInfo()

    def calcSWSuitabilityIndex(self, df, weights):

        w_d = weights['duration'].iloc[0]
        w_t = weights['timing'].iloc[0]
        w_f = weights['dry'].iloc[0]

        duration = (w_d * df['flood_duration'])
        timing = (w_t * df['flood_timing'])
        dry = (w_f * df['flood_dry_period'])

        # df = pd.DataFrame(dict(duration=duration, timing=timing, dry=dry) )

        return duration+timing+dry

    #End calcSWSuitabilityIndex()
    
    def eventIndexWeightedAvg(self, flood_events_df, weights):
        """
        Calculate flood index summary based on weighted average for each event
        Output attributes:
        event id, start date, end date, summary flood index
        """

        flood_events_df['flood_index_weightavg'] = flood_events_df['duration_index']*weights['duration'] + \
                                                  flood_events_df['timing_index']*weights['timing'] + \
                                                  flood_events_df['dry_index']*weights['dry']

        return flood_events_df

    #End eventIndexWeightedAvg()
        
    def eventIndexMin(self, flood_events_df):
        """
        Calculate flood index summary based on min rule
        Output attributes:
        event id, start date, end date, summary flood index
        """
        flood_events_df['flood_index_min'] = flood_indexes.apply(lambda x: min(x["duration_index"], x["timing_index"], x["dry_index"]), axis=1)
        
        return flood_events_df
    #End eventIndexMin()

        
    def flowIndex(self, flow_df, flood_events_df, aggregate_option):
        """
        Calculate daily flow index based on event index
        Output attributes:
        Date, flow_index

        :returns: Pandas Dataframe of flow indexes
        """

        flow_index = pd.DataFrame(dict(flow_index=flow_df["Flow"]), index=flow_df.index)
        
        flow_index["flow_index"] = flood_events_df[(flow_index.index >= flood_events_df["start_date"]) & (flow_index.index <= flood_events_df["end_date"])][aggregate_option]
        
        return flow_index

    #End flowIndex

    def ceaseDays(self, df, **kwargs):

        """
        Determine the number of days flow stopped
        """

        ceaseflow = lambda x: x.dropna()[x == 0].count()

        grouping = df.groupby(df.index.year)

        return grouping.apply(ceaseflow)
    #End ceaseDays()

    def ctfDays(self, df, ctf=4000, **kwargs):

        flooddays = lambda x, ctf: x.dropna()[x > ctf].count() #[x > ctf].count()

        #Original R code:
        #summaryby <- as.POSIXlt(time(x))$year + 1900
        #Gets number of years since 1900, then adds 1900 years
        grouping = df.groupby(df.index.year)

        return grouping.apply(func=flooddays, ctf=ctf)
    #End ctfDays

    def ctfEvents(self, df, ctf=4000, min_separation=5, min_duration=1, **kwargs):

        flow_events = self.floodEvents(df, threshold=ctf, min_duration=min_duration, min_separation=min_separation)

        # print flow_events
        # print "-=-=-=-=-=-=-=-"

        return flow_events
        
    #End ctfEvents()



    #get first row out of matching rows
    # low_ctf = self.getAssetParam(asset_table, gauge, "CTF_low")

    # ctf_low_days = self.ctfDays(surfaceflow, \
    #     threshold=low_ctf, \
    #     min_separation=min_gap, \
    #     min_duration=min_size)

    # ctf_low_events = self.ctfEvents(surfaceflow, \
    #     threshold=low_ctf, \
    #     min_separation=min_gap, \
    #     min_duration=min_size)
    
    # mid_ctf = self.getAssetParam(asset_table, gauge, "CTF_mid")
    # ctf_mid_days = self.ctfDays(surfaceflow, \
    #     threshold=mid_ctf, \
    #     min_separation=min_gap, \
    #     min_duration=min_size)

    # ctf_mid_events = self.ctfEvents(surfaceflow, \
    #     threshold=mid_ctf, \
    #     min_separation=min_gap, \
    #     min_duration=min_size)

    # high_ctf = self.getAssetParam(asset_table, gauge, "CTF_high")
    # ctf_high_days = self.ctfDays(surfaceflow, \
    #     threshold=high_ctf, \
    #     min_separation=min_gap, \
    #     min_duration=min_size)

    # ctf_high_events = self.ctfEvents(surfaceflow, \
    #     threshold=high_ctf, \
    #     min_separation=min_gap, \
    #     min_duration=min_size )


