from integrated.Modules.Core.IntegratedModelComponent import Component

class WaterSources(Component):

    """
    Represents a source of water
    """

    def __init__(self, **kwargs):

        if 'water_source' not in kwargs:
            raise KeyError('Required dict water_source not found')
        else:

            if type(kwargs['water_source']) is not dict:
                raise TypeError('water_source is supposed to be a dictionary')

        #End if

        #Set all kwargs as class attributes
        for key, value in kwargs.items():
            setattr(self, key, value)
        #End For

    #End init()

    def calcGrossWaterAvailable(self):

        return sum(self.water_source.values())

    #End calculateNetAvailableWater()

    def updateWaterLevel():
        pass
    #End updateWaterLevel()

    def extractWater():
        pass
    #End extractWater()

    # def calcTotalWaterInput(self):
    #     total = 0

    #     for source in self.water_source:
    #         total = total + self.water_source[source]
    #     #End for

    #     return total
    # #End calcTotalWaterInput()
        

#End WaterSources
