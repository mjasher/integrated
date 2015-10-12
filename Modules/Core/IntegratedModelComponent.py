class Component(object):

    """
    Model Component Object.
      All model components should inherit (or implement their own versions) of the methods defined here.
    """

    def __init__():
        pass
    #End __init__()

    def setMethod(self, name, func):

        """
        Assign the given method to the given attribute name.

        Example::

            Test = Component()
            
            #Defining an example function
            def example_function(x):
                return x*x
            #End example_function()

            #Assign the function to a variable
            example = example_function

            #Set the function as a Class method
            Component.setMethod('new_function', example)

            print Component.new_function(5)

            #The above should print out '25'

        :returns: True on success, False on failure

        """
        
        try:
            setattr(self, name, func)
            return True
        except:
            return False


    #End setMethod()

    def loadParamSet(self, param_set):

        """
        Loads in parameters from the given ParameterSet object

        WARNING: Does not clear previously set custom attributes or methods unless explicitly included in the given ParameterSet

        """

        params = param_set.getParams()

        for attribute in params:
            setattr(self, attribute, params[attribute])
        #End for

    #End

    def loadComponentParams(self, component, comp_name, params):

        comp = getattr(self, component)

        comp[comp_name].loadParams(params)
    #End loadComponentParams

    def setParam(self, **kwargs):

        """

        Set a component attribute

        :param component: object that represents a (store/irrigation/etc)
        :param subcomponent: (optional) as above
        :param comp_name: name of component, e.g. flood, FarmDam, etc.
        :param attr_name: attribute to modify
        :param amount: value to assign to attribute
        :returns: value of modified attribute

        """

        #Type of farm component (storage, crop, irrigation)
        component = kwargs['component']

        #Name of component (or first one found in components if not specified)
        comp_name = kwargs['comp_name'] if 'comp_name' in kwargs else getattr(self, component).keys()[0]

        #Name of attribute to modify
        attr_name = kwargs['attr_name']

        #Amount to modify attribute to
        amount = kwargs['amount']

        #Get farm component collection (storages, crops, irrigations, etc.)
        component = getattr(self, component)

        if 'subcomponent' in kwargs and kwargs['subcomponent'] is not None:
            subcomponent = kwargs['subcomponent']
            comp = getattr(component[comp_name], subcomponent)
        else:
            comp = component[comp_name]

        #set parameter for given farm component
        setattr(comp, attr_name, amount)

        return getattr(comp, attr_name)

    #End

    def getParam(self, **kwargs):

        """
        Gets the value of a specific attribute.

        kwargs are expected in the format as given in setParam()

        :param component: object that represents a (store/irrigation/etc)
        :param subcomponent: (optional) as above
        :param comp_name: name of component, e.g. flood, FarmDam, etc.
        :param attr_name: attribute to modify
        :param amount: value to assign to attribute
        :returns: value of modified attribute
        """

        component = kwargs['component']
        comp_name = kwargs['comp_name'] if 'comp_name' in kwargs else getattr(self, component).keys()[0]
        attr_name = kwargs['attr_name']

        #Get farm component collection (storages, crops, irrigations, etc.)
        comp = getattr(self, component)

        if 'subcomponent' in kwargs and kwargs['subcomponent'] is not None:
            subcomponent = kwargs['subcomponent']
            comp = getattr(comp[comp_name], subcomponent)
        else:
            comp = comp[comp_name]

        try:
            val = getattr(comp, attr_name)
        except AttributeError:
            return None

        #set parameter for given farm component
        return val

    #End getParam()

    def getNumParams(self):

        """
        Count total number of parameters for this object

        :returns: number of parameters
        :return type: int
        """

        return len(dir(self))

    #End getNumParams()

    # def resetParams(self):

    #     #Reset parameters for each store
    #     for store in self.storages:
    #         self.storages[store].resetParams()
    #     #End for

    #     for irrig in self.irrigations:
    #         self.irrigations[irrig].resetParams()

    #     for crop in self.crops:
    #         self.crops[crop].resetParams()

    # #End resetParams()

#End IntegratedModelComponent()