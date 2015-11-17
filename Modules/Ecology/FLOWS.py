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
    
u    def 