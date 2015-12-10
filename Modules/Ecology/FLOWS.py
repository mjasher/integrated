#FLOWS.py

class FLOWS:
    
    """
    Model how well a flow regime matches environmental flow requirements, based on FLOWS recommendationss. 
    The model does not involve groundwater.
    """
    
    def __init__(self, **kwargs):

        """
        eco_site: ecological model site
        """

        self.eco_site = kwargs.pop('eco_site','1')  
        
        #End init()
    
    def FlowsCategory (self, flow, flows_thresholds):
        """
        convert flow daily time series into FLOWS category:
        summer cease to flow, summer low flow, summer fresh
        winter low flow, winter high flow, winter bankfull flow, winter overbank flow
        Input: daily flow (Date, ML/d); thresholds for each type of flows (input csv)
        Output: daily FLOWS category (Date, flows_cat)
        """
        return flows_cat
        
    def FlowsAnnualSummary (self, flows_cat, flows_dur_req):
        """
        convert daily FLOWS category (Date, flows_cat) into annual summary
        summer cease to flow/summer low flow/winter low flow: calculate the number of days in a year
        summer fresh/winter high/winter bankfull/winter overbank: calculate the number of event meet duration requirements
        Input: flows_cat, flows duration requirement
        Output: annual summary of FLOWS (year, days/events)
        """
        return flows_annual_sum
        
    def FlowsAnnualComplience (self, flows_annual_sum, flows_freq_req):
        """
        calculate the annual complience of FLOWS requirement
        Input: annual summary of FLOWS, flows_freq_req
        Output: Percentage of days/events matches flows requirement (Year, cease_to_flow, etc)
        """
        return flows_annual_com
        
        
        
        