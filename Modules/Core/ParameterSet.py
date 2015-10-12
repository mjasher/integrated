class ParameterSet(object):

    """
    Holds parameters to configure integrated model components
    """

    def __init__(self, **kwargs):

        #Set all key word arguments as attributes
        for key, value in kwargs.items():
            setattr(self, key, value)
        #End For
    #End __init__()

    def getParams(self):

        """
        Gets all parameters within the set

        :returns: a Dict of all parameters/attributes
        :return type: Dict

        """

        params = {}
        for key, value in self.__dict__.iteritems():
            params[key] = value
        #End For

        return params
    #End getParameters()

    def getNumParams(self):

        """
        Get total number of parameters

        :returns: Number of parameters 
        :return type: int
        """

        return len(dir(self))
    #End numParameters()



#End ParameterSet
