"""
Defines parameters to use for the Farm Model.

Running this file by itself will not work.

This is intended to be imported by a top-level script/package.

TODO: Split out non-farm model related stuff
      Import settings from CSV or JSON?

"""


#import ClimateVariables

from integrated.Modules.Core.ParameterSet import *
from integrated.Modules.Farm.WaterSources import WaterSources

from integrated.Modules.Farm.Irrigations.IrrigationPractice import IrrigationPractice
from integrated.Modules.Core.GeneralFunctions import *
from integrated.Modules.Farm.Crops.CropInfo import CropInfo

#Water sources in MegaLitres
#200ML = 20-25% of average long term seasonal balance for regulated surface water licences on the Namoi river
#p. 14, Powell & Scott (representative farm, but double check with Arshad 2014)
WATER_SOURCE = {'flood_harvest': 200}
Water = WaterSources(water_source={'flood_harvest': 200})

#Climate Variables
#I thought there would be more, so used a ParameterSet.
#Climate = ParameterSet(surface_evap_rate=0.4)

FarmDam_params = ParameterSet(
    include_farm_dam_capital_costs=False,
    name='Farm Dam',
    num_years=30,
    storage_capacity_ML=200,
    storage_cost_per_ML=1000,
    cost_capital=0,
    pump_vol_ML=0,
    maintenance_rate=0.005,
    capture_pump_cost_ratio=0.5,
    pump_cost_dollar_per_ML=35,
    ClimateVariables=ParameterSet(surface_evap_rate=0.4),
    WaterSources=WaterSources(water_source={'flood_harvest': 200})
)

Dam_params = ParameterSet(
    include_farm_dam_capital_costs=False,
    name='Regional Dam',
    num_years=50,
    storage_capacity_ML=200,
    storage_cost_per_ML=1000,
    cost_capital=0,
    pump_vol_ML=0,
    maintenance_rate=0.0,
    capture_pump_cost_ratio=0.0,
    pump_cost_dollar_per_ML=35,
    ClimateVariables=ParameterSet(surface_evap_rate=0.4),
    WaterSources=WaterSources(water_source={'flood_harvest': 200})
)

SurfaceWater_params = ParameterSet(
        name='SurfaceWater',
        water_level=50.0
    )
Groundwater_params = ParameterSet(
        name='Groundwater',
        water_level=50.0
    )


Basin_params = ParameterSet(
    name='Basin',
    num_years=30,
    storage_capacity_ML=200,
    storage_cost_per_ML=0,
    cost_capital=0,
    maintenance_rate=0.1,
    capture_pump_cost_ratio=0.6,
    pump_cost_dollar_per_ML=35,
    ClimateVariables=ParameterSet(surface_evap_rate=0.4),
    WaterSources=WaterSources(water_source={'flood_harvest': 200})
)

ASR_params = ParameterSet(
    name='ASR',
    num_years=20,
    storage_capacity_ML=200,
    storage_cost_per_ML=0,
    capital_cost_per_ML_at_02_per_day=700, #TESTING, REMOVE WHEN DONE
    cost_capital=0,
    maintenance_rate=0.07,
    capture_pump_cost_ratio=0.6,
    pump_cost_dollar_per_ML=35,
    ClimateVariables=ParameterSet(surface_evap_rate=0.4),
    WaterSources=WaterSources(water_source={'flood_harvest': 200})
)

#Create irrigation strategies
Flood_params = ParameterSet(
    name='Flood',
    irrigation_rate=1,
    irrigation_efficiency=0.55,
    lifespan=10,
    cost_per_Ha=0.0,
    replacement_cost_per_Ha=2500.0
)
Flood = IrrigationPractice(**Flood_params.getParams())

Spray_params = ParameterSet(
    name='Spray',
    irrigation_rate=1,
    #0.8 From Smith, NSW DPI agronomist, table of comparative irrigation costs and from Ticehurst et al. under review, p 6
    irrigation_efficiency=0.8,
    lifespan=15,
    #2000-3000 River, 2500-3500 Bore, Smith, NSW DPI agronomist 2012, table of comparative irrigation costs
    cost_per_Ha=2500
)

Drip_params = ParameterSet(
    name='Drip',
    irrigation_rate=1,
    #0.85 from Smith and from Ticehurst et al. under review, p 6
    irrigation_efficiency=0.85,
    lifespan=15,
    #6000 - 9000 Smith, NSW DPI agronomist 2012, table of comparative irrigation costs
    cost_per_Ha=6000
)

#Create crops
Cotton_params = ParameterSet(
    crop_name='Cotton',
    #price per yield (538) Taken from original code
    price_per_yield=538,
    yield_per_Ha=9.5,
    water_use_ML_per_Ha=7.9, #7.9 (value as found in Arshad et al. 2013) * 0.55 (average flood irrigation efficiency) = 4.345 #6.004 (figure based on 7.9 * 0.76 => national average),
    #Cotton.water_use_ML_per_Ha = 7.59 #Taken from Montegomery & Bray, Figure 1, p 5
    #variable cost taken from original code. 153.1 represents pigeon pea, sacrificial crop (uses ~5% of land)
    variable_cost_per_Ha=2505+153.1,
    root_depth_m=0.55,
    depletion_fraction=0.4,
)
Cotton = CropInfo(**Cotton_params.getParams())

#WARNING: THE NUMBERS BELOW ARE ALL MADE UP
Wheat_params = ParameterSet(
    crop_name='Wheat',
    price_per_yield=400,
    yield_per_Ha=12,
    water_use_ML_per_Ha=3.0,
    variable_cost_per_Ha=2000.0,
    planting_info={
        'seed': ['09-01', 0.4],
        'plant': ['11-01', 0.85],
        'harvest': ['01-31', 0.6]
    },
    root_depth_m=0.55,
    depletion_fraction=0.4,
)

Canola_params = ParameterSet(
    crop_name='Canola',
    price_per_yield=350,
    yield_per_Ha=11,
    water_use_ML_per_Ha=3.0,
    variable_cost_per_Ha=1800.0,
    planting_info={
        'seed': ['09-01', 0.4],
        'plant': ['11-01', 0.85],
        'harvest': ['01-31', 0.6]
    },
    root_depth_m=0.55,
    depletion_fraction=0.4,
)

#Seed in September-October, planting in November
#Start harvesting from late January to end of March
#http://www.mmg.com.au/local-news/country-news/processing-tomato-harvest-beats-last-year-1.90835
Tomato_params = ParameterSet(
    crop_name='Tomato',
    price_per_yield=600,
    yield_per_Ha=8,
    water_use_ML_per_Ha=6.0,
    #when to plant Month-Day, #Crop coefficient at plant stages
    planting_info={
        'seed': ['09-01', 0.4],
        'plant': ['11-01', 0.85],
        'harvest': ['01-31', 0.6]
    },
    root_depth_m=0.55,
    depletion_fraction=0.4,
    variable_cost_per_Ha=2150.0,
)

Light_clay_params = ParameterSet(
    name='Light Clay',
    TAW_mm=180
)

MIN_BOUND = 0.3
MAX_BOUND = 0.95
BOUNDS = {'min': MIN_BOUND, 'max': MAX_BOUND, 'static': False, 'base': False}

BASE_FARM = ParameterSet(
    name='Test Farm',
    storages={},
    water_sources=dict(surface_water=0.0, groundwater=0.0, precipitation=0.0, dam=10000.0),
    irrigations={'Flood': ParameterSet(**Flood_params.getParams())},
    crops={'Wheat': CropInfo(**Wheat_params.getParams()), 'Canola': CropInfo(**Canola_params.getParams()), 'Tomato': CropInfo(**Tomato_params.getParams())}
    #bounds={'min': 0.3, 'max': 0.95, 'static': False, 'base': True}
)
