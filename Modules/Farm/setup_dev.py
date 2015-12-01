"""
Defines parameters to use for the Farm Model.

Running this file by itself will not work.

This is intended to be imported by a top-level script/package.

TODO: Split out non-farm model related stuff
      Import settings from CSV or JSON?

"""


#import ClimateVariables

from integrated.Modules.Core.ParameterSet import *
from integrated.Modules.WaterSources import WaterSources

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
    replacement_cost_per_Ha=2500.0,
    maintenance_rate=0.02 
    #Pipe and Riser irrigation system: www.murraydairy.com.au/LiteratureRetrieve.aspx?ID=138617
    #2% maintenance rate seems to be the usual assumed value, as it is the value used in Arshad et al. (2013) and others
)
Flood = IrrigationPractice(**Flood_params.getParams())

Spray_params = ParameterSet(
    name='Spray',
    irrigation_rate=1,
    #0.8 From Smith, NSW DPI agronomist, table of comparative irrigation costs and from Ticehurst et al. under review, p 6
    irrigation_efficiency=0.8,
    lifespan=15,
    #2000-3000 River, 2500-3500 Bore, Smith, NSW DPI agronomist 2012, table of comparative irrigation costs
    cost_per_Ha=2500,
    maintenance_rate=0.02
)

Drip_params = ParameterSet(
    name='Drip',
    irrigation_rate=1,
    #0.85 from Smith and from Ticehurst et al. under review, p 6
    irrigation_efficiency=0.85,
    lifespan=15,
    #6000 - 9000 Smith, NSW DPI agronomist 2012, table of comparative irrigation costs
    cost_per_Ha=6000,
    maintenance_rate=0.02
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

#Crop Coefficients for French-Schultz taken from
#http://www.bcg.org.au/cb_pages/files/Explination%20N%20Budgeting.pdf
#unless stated otherwise

#Crop Coefficients at different stages
#Root depth
#http://www.fao.org/nr/water/cropinfo_wheat.html

#WARNING: THE NUMBERS BELOW ARE A MIX OF DUMMY AND POSSIBLE VALUES
Wheat_params = ParameterSet(
    crop_name='Wheat',
    price_per_yield=480,
    yield_per_Ha=2.5, #tonnes/Ha as given in Jarrod Lukeys 2014, emailed by Rabi
    water_use_ML_per_Ha=3.0, #Given in Goulburn Broken CMA water savings calculator
    variable_cost_per_Ha=1000.0,
    planting_info={
        'seed': ['09-01', 0.5],
        'plant': ['11-01', 0.5],
        'harvest': ['01-31', 0.8]
    },
    root_depth_m=0.3,
    depletion_fraction=0.4,
    et_coef=110, #Crop Evapotranspiration coefficient 110 mm
    wue_coef=20, #Crop WUE coefficient for French-Schultz
)

Canola_params = ParameterSet(
    crop_name='Canola',
    price_per_yield=513,
    #yield_per_Ha=1.5, #tonnes/Ha, as given in Jarrod Lukeys 2014, emailed by Rabi
    yield_per_Ha=2.5, #target yield, as given in http://agriculture.vic.gov.au/agriculture/grains-and-other-crops/crop-production/growing-canola
    water_use_ML_per_Ha=6.0, #Given in Goulburn Broken CMA water savings calculator
    variable_cost_per_Ha=1000.0,
    planting_info={
        'seed': ['09-01', 0.1],
        'plant': ['11-01', 1.1],
        'harvest': ['01-31', 0.35]
    },
    root_depth_m=0.55,
    depletion_fraction=0.4,
    et_coef=110, #Crop Evapotranspiration coefficient 110 mm DUMMY VALUE FOR DEV PURPOSES!
    wue_coef=15, #Crop WUE coefficient for French-Schultz
)

#Seed in September-October, planting in November
#Start harvesting from late January to end of March
#http://www.mmg.com.au/local-news/country-news/processing-tomato-harvest-beats-last-year-1.90835

#Crop Yield in Tonnes/Ha
#http://agriculture.vic.gov.au/agriculture/horticulture/vegetables/vegetable-growing-and-management/vegetable-growing
#http://agriculture.vic.gov.au/agriculture/grains-and-other-crops/crop-production/growing-wheat

#Root depth and crop coefficents for growth stages
#http://agriculture.vic.gov.au/agriculture/horticulture/vegetables/vegetable-growing-and-management/estimating-vegetable-crop-water-use

Tomato_params = ParameterSet(
    crop_name='Processing Tomato',
    price_per_yield=460,
    yield_per_Ha=49.4,
    water_use_ML_per_Ha=6.0, #Given in Goulburn Broken CMA water savings calculator
    #when to plant Month-Day, #Crop coefficient at plant stages
    planting_info={
        'initial': ['09-01', 0.5],
        'development': ['10-01', 0.7],
        'mid-season': ['11-01', 1.1],
        'late': ['12-01', 0.95],
        'harvest': ['01-31', 0.6]
    },
    root_depth_m=1.0,
    depletion_fraction=0.4,
    variable_cost_per_Ha=10000.0, #https://www.daf.qld.gov.au/plants/fruit-and-vegetables/vegetables/tomatoes/harvesting-and-marketing-tomatoes
    et_coef=90,
    wue_coef=10, 
)

#Values for soil TAW taken from
#http://agriculture.vic.gov.au/agriculture/horticulture/vegetables/vegetable-growing-and-management/estimating-vegetable-crop-water-use
Light_clay_params = ParameterSet(
    name='Light Clay',
    TAW_mm=172,
    current_TAW_mm=10
)

Clay_loam_params = ParameterSet(
    name='Clay Loam',
    TAW_mm=164,
    current_TAW_mm=30
)

Loam_params = ParameterSet(
    name='Loam',
    TAW_mm=164,
    current_TAW_mm=25
)

MIN_BOUND = 0.3
MAX_BOUND = 0.95
BOUNDS = {'min': MIN_BOUND, 'max': MAX_BOUND, 'static': False, 'base': False}

import copy
BASE_FARM = ParameterSet(
    name='Test Farm',
    storages={},
    water_sources=dict(surface_water=0.0, groundwater=0.0, precipitation=0.0, dam=10000.0),
    irrigations={'Flood': ParameterSet(**Flood_params.getParams())},
    crops={'Wheat': CropInfo(**Wheat_params.getParams()), 'Canola': CropInfo(**Canola_params.getParams()), 'Tomato': CropInfo(**Tomato_params.getParams())}
    #bounds={'min': 0.3, 'max': 0.95, 'static': False, 'base': True}
)
