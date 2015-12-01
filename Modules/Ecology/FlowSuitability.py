# FlowSuitability.py

import WaterSuitability

class FlowSuitability(object):
        
    def floodEvents(self, flow, threshold, min_separation, min_duration):
        """
        Create a list of flood events based on daily flow, like hydromad eventseq
        Output attributes:
        event id, start date, end date, duration, month of start date, interflood dry period
        """
        return flood_events
    
    def FloodIndexes(self, flood_events):
        """
        Calculate index for each flood attribute based on index curve (defined in WaterSuitability.py)
        Output attributes:
        event id, start date, end date, duration index, timing index, interflood dry period index
        """
        return flood_indexes
    
    
    def EventIndexWeightedAvg(self,flood_indexes):
        """
        Calculate flood index summary based on weighted average for each event
        Output attributes:
        event id, start date, end date, summary flood index
        """
        return event_index
        
    def EventIndexMin(self,flood_indexes):
        """
        Calculate flood index summary based on min rule
        Output attributes:
        event id, start date, end date, summary flood index
        """
        return event_index   
        
    def FlowIndex(self,event_index):
        """
        Calculate daily flow index based on event index
        Output attributes:
        Date, flow_index
        """
        return flow_index