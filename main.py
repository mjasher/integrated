import datetime
import Modules

from random import uniform

"""
Main script in development
This is the "Master" script that calls all other modules and handles their interactions
"""

if __name__ == "__main__":
    import Setup.FarmModel_setup as FarmConfig

    from integrated.Modules.Farm.Farms.FarmInfo import FarmInfo
    from integrated.Modules.Farm.Farms.Management import FarmManager
    from integrated.Modules.Farm.Fields.Field import FarmField
    from integrated.Modules.Farm.Fields.Soil import SoilType
    
    pass
#End if