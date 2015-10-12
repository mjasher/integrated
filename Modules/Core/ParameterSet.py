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

        :returns: a dict of all parameters/attributes

        """

        params = {}
        for key, value in self.__dict__.iteritems():
            params[key] = value
        #End For

        return params
    #End getParameters()

    def getNumParams(self):

        """
        Count total number of parameters

        :returns: (int) Number of parameters 
        """

        return len(dir(self))
    #End numParameters()



#End ParameterSet
