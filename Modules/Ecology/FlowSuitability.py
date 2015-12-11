# FlowSuitability.py

import WaterSuitability

class FlowSuitability(object):
        
    def floodEvents(self, flow, threshold, min_separation, min_duration):
        """
        Create a list of flood events based on daily flow, like hydromad eventseq
        Output attributes:
        event id, start date, end date, duration, startmonth (month when the event start), dry (interflood dry period)
        """
        
        return flood_events_df
    
    def FloodIndexes(self, flood_events_df, coordinates):
        """
        Calculate index for each flood attribute based on index curve (defined in WaterSuitability.py)
        input: coordinates is a dict of duration, timing, dry coordinates
        Output attributes:
        event id, start date, end date, duration, startmonth (month when the event start), dry (interflood dry period),duration index, timing index, interflood dry period index
        """

        duration = coordinates["duration"]
        timing = coordinates["timing"]
        dry = coordinates["dry"]
        
        #flood_indexes = flood_events_df.copy()
        flood_events_df['duration_index'] = np.interp(flood_events_df.duration, duration.x, duration.y)
        flood_events_df['timing_index'] = np.interp(flood_events_df.startmonth, timing.x, timing.y)
        flood_events_df['dry_index'] = np.interp(flood_events_df.dry, dry.x, dry.y)
        
        return flood_events_df
    
    
    def EventIndexWeightedAvg(self,flood_events_df, weights):
        """
        Calculate flood index summary based on weighted average for each event
        Output attributes:
        event id, start date, end date, summary flood index
        """
        flood_events_df['flood_index_weightavg']= flood_events_df['duration_index']*weights['duration']+flood_events_df['timing_index']*weights['timing']+flood_events_df['dry_index']*weights['dry']
        return flood_events_df
        
    def EventIndexMin(self,flood_events_df):
        """
        Calculate flood index summary based on min rule
        Output attributes:
        event id, start date, end date, summary flood index
        """
        flood_events_df['flood_index_min'] = flood_indexes.apply(lambda x: min(x["duration_index"], x["timing_index"], x["dry_index"]), axis=1)
        
        return flood_events_df   
        
        
    def FlowIndex(self, flow_df, flood_events_df, aggregate_option):
        """
        Calculate daily flow index based on event index
        Output attributes:
        Date, flow_index
        """

        flow_index = pd.DataFrame(flow_df["Flow"], index=flow_df.index)
        flow_index["Flow"] = 0
        flow_index.columns = ["flow_index"]
        
        flow_index["flow_index"] = flood_events_df[(flow_index.index >= flood_events_df["start_date"]) & (flow_index.index <= flood_events_df["end_date"])][aggregate_option]
        
        #flood_events_df['flood_index_sum']
        
        return flow_index