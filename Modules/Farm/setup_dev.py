"""
Defines parameters to use for the Farm Model.

Running this file by itself will not work.

This is intended to be imported by a top-level script/package.

TODO: Split out non-farm model related stuff
      Import settings from CSV or JSON?

"""


#import ClimateVariables
from integrated.Modules.Core.GeneralFunctions import *
from integrated.Modules.Core.ParameterSet import *
from integrated.Modules.Core.Handlers.FileHandler import FileHandler

from integrated.Modules.WaterSources import WaterSources

from integrated.Modules.Farm.Irrigations.IrrigationPractice import IrrigationPractice
from integrated.Modules.Farm.Crops.CropInfo import CropInfo

#Water sources in MegaLitres
#200ML = 20-25% of average long term seasonal balance for regulated surface water licences on the Namoi river
#p. 14, Powell & Scott (representative farm, but double check with Arshad 2014)
WATER_SOURCE = {'flood_harvest': 200}
#Water = WaterSources(water_source={'flood_harvest': 200}, pumping_cost=40)

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
    # WaterSources=WaterSources(water_source={'flood_harvest': 200})
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
    # WaterSources=WaterSources(water_source={'flood_harvest': 200})
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
    # WaterSources=WaterSources(water_source={'flood_harvest': 200})
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
    # WaterSources=WaterSources(water_source={'flood_harvest': 200})
)

#Create irrigation strategies
Flood_params = ParameterSet(
    name='Flood',
    irrigation_rate=1,
    irrigation_efficiency=0.55,
    lifespan=10,
    cost_per_Ha=0.0,
    replacement_cost_per_Ha=2000.0,
    maintenance_rate=0.02 
    #Pipe and Riser irrigation system: www.murraydairy.com.au/LiteratureRetrieve.aspx?ID=138617
    #2% maintenance rate seems to be the usual assumed value, as it is the value used in Arshad et al. (2013) and others
)
Flood = IrrigationPractice(**Flood_params.getParams())

PipeAndRiser = IrrigationPractice(**Flood_params.getParams())
PipeAndRiser.name = 'Pipe and Riser'

#DUMMY VALUES
PipeAndRiser.irrigation_efficiency = 0.74
PipeAndRiser.lifespan = 10
PipeAndRiser.cost_per_Ha=0.0 #3300 / Ha "Pipe and risers irrigation system: is it a good investment" DEPI 2013
PipeAndRiser.replacement_cost_per_Ha=3300 #Assume PipeAndRiser already installed.
PipeAndRiser.pumping_cost=15


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
Spray = IrrigationPractice(**Spray_params.getParams())
Spray.cost_per_Ha=0.0

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
Drip = IrrigationPractice(**Drip_params.getParams())


### Import data from files ###

DataHandle = FileHandler()

crop_data_files = DataHandle.importFiles('Crops/data/variables', walk=True, index_col=0, skipinitialspace=True)

crop_data = {}
crop_params = {}
for folder in crop_data_files:
    for crop_name in crop_data_files[folder]:
        crop_data[crop_name] = crop_data_files[folder][crop_name]

        temp_data = crop_data[crop_name]['Best Guess'].to_dict()
        temp_data['crop_name'] = crop_name
        crop_params[crop_name] = ParameterSet(**temp_data)
    #End for
#End for

crop_coefficients = DataHandle.importFiles('Crops/data/coefficients', index_col=0, skipinitialspace=True)
for folder in crop_coefficients:
    for crop_name in crop_coefficients[folder]:
        crop_params[crop_name].planting_info = crop_coefficients[folder][crop_name] 
    #End for
#End for

#Values for soil TAW taken from
#http://agriculture.vic.gov.au/agriculture/horticulture/vegetables/vegetable-growing-and-management/estimating-vegetable-crop-water-use
Light_clay_params = ParameterSet(
    name='Light Clay',
    TAW_mm=172,
    current_TAW_mm=35
)

Clay_loam_params = ParameterSet(
    name='Clay Loam',
    TAW_mm=164,
    current_TAW_mm=15
)

Loam_params = ParameterSet(
    name='Loam',
    TAW_mm=164,
    current_TAW_mm=10
)

MIN_BOUND = 0.3
MAX_BOUND = 0.95
BOUNDS = {'min': MIN_BOUND, 'max': MAX_BOUND, 'static': False, 'base': False}

BASE_FARM = ParameterSet(
    name='Test Farm',
    storages={},
    water_sources={}, #dict(surface_water=0.0, groundwater=0.0, precipitation=0.0, dam=10000.0),
    irrigations={'Flood': ParameterSet(**Flood_params.getParams())},
    crops={crop_name: CropInfo(**cp.getParams()) for crop_name, cp in crop_params.iteritems()}
    #bounds={'min': 0.3, 'max': 0.95, 'static': False, 'base': True}
)