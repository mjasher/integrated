import copy

class ParameterSet(object):

    """
    Holds parameters to configure integrated model components
    """

    def __init__(self, **kwargs):

        #Set all key word arguments as attributes
        for key, value in kwargs.items():
            setattr(self, key, copy.deepcopy(value))
        #End For
    #End __init__()

    def getParams(self):

        return copy.deepcopy(self.__dict__)

    def getNumParams(self):

        """
        Get total number of parameters

        :returns: Number of parameters 
        :return type: int
        """

        return len(dir(self))
    #End numParameters()



#End ParameterSet
