
from integrated.Modules.Core.IntegratedModelComponent import Component

class SurfaceWaterPolicy(Component):
    

    def __init__(self, Climate, **kwargs):

        self.Climate = Climate

        #Set all kwargs as class attributes
        for key, value in kwargs.items():
            setattr(self, key, value)
        #End For
        
    #End init()

    def determineAnnualAllocation(self, prev_rainfall, alloc=[0, 1]):

        """
        Determine surface water allocation based on previous rainfall.
        Adapted from Maules Creek model

        :param prev_rainfall: (int) Previous year's rainfall in mm
        :param alloc: (array-like) Min and Max allocations (0 - 1) possible

        :returns: (float) percent allocation (0 to 1)
        """

        min_alloc, max_alloc = alloc

        if prev_rainfall >= self.Climate.high_rainfall:
            return max_alloc
        else:
            #otherwise, the allocation is a linear relationship with annual rainfall.
            return min_alloc + (max_alloc - min_alloc) * (prev_rainfall - self.Climate.min_rainfall) / (self.Climate.high_rainfall - self.Climate.min_rainfall)
        #End if

    #End determineAnnualAllocation()

    def calcDeficit(self, sw_alloc, allocatable_water):

        """
        Calculate water deficit from this water source due to surface water allocation
        Adapted from Maules Creek model

        :param sw_alloc: Surface water allocation (0 to 1)
        :param allocatable_water: Total amount of water that can be allocated to the farmer. Under usual circumstances this can be equal to the farmer's water entitlement
        """

        sw_deficit = max(0.0, 1.0 - sw_alloc) * allocatable_water

        return sw_deficit

    #End calcDeficit()

#End class()
