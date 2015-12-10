# FlowSuitability.py

import WaterSuitability

class FlowSuitability(object):
        
    def floodEvents(self, flow, threshold, min_separation, min_duration):
        """
        Create a list of flood events based on daily flow, like hydromad eventseq
        Output attributes:
        event id, start date, end date, duration, startmonth (month when the event start), dry (interflood dry period)
        """
        
        return flood_events
    
    def FloodIndexes(self, flood_events, coordinates):
        """
        Calculate index for each flood attribute based on index curve (defined in WaterSuitability.py)
        Output attributes:
        event id, start date, end date, duration index, timing index, interflood dry period index
        """
        flood_indexes = flood_events
        flood_indexes['duration_index'] = np.interp(flood_events.duration, duration.coordinate_x, duration.coordinate_y)
        flood_indexes['timing_index'] = np.interp(flood_events.startmonth, timing.coordinate_x, timing.coordinate_y)
        flood_indexes['dry_index'] = np.interp(flood_events.dry, dry.coordinate_x, dry.coordinate_y)
        
        return flood_indexes
    
    
    def EventIndexWeightedAvg(self,flood_indexes, weights):
        """
        Calculate flood index summary based on weighted average for each event
        Output attributes:
        event id, start date, end date, summary flood index
        """
        event_index = flood_indexes
        event_index['flood_index_sum']= flood_indexes['duration_index']*weights['duration']+flood_indexes['timing_index']*weights['timing']+flood_indexes['dry_index']*weights['dry']
        return event_index
        
    def EventIndexMin(self,flood_indexes):
        """
        Calculate flood index summary based on min rule
        Output attributes:
        event id, start date, end date, summary flood index
        """
        event_index = flood_indexes
        event_index['flood_index_sum']= min(flood_indexes['duration_index'],flood_indexes['timing_index'],flood_indexes['dry_index'])        
        return event_index   
        
        
    def FlowIndex(self,event_index):
        """
        Calculate daily flow index based on event index
        Output attributes:
        Date, flow_index
        """
        return flow_index