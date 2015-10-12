# from WaterSources import WaterSources
# #import Farms.WaterStorages

# from Farms import FarmInfo

# print FarmInfo

# # import inspect
# # funcs = inspect.getmembers(Farms, inspect.isfunction)
# # print funcs

# #import ClimateVariables

# from Core.ParameterSet import *
# from Irrigation.IrrigationPractice import IrrigationPractice
# from Farm.GeneralFunctions import *
# import Farm.CropInfo

# water_sources = {"flood_harvest": 200, "initial": 1000, "previous": 0, "current": 0}
# #Water = WaterSources(water_source=water_sources)

# #Water sources in MegaLitres
# #200ML = 20-25% of average long term seasonal balance for regulated surface water licences on the Namoi river
# #p. 14, Powell & Scott (representative farm, but double check with Arshad 2014)
# #WATER_SOURCE = {'flood_harvest': 200}
# #Water = WaterAvailability.WaterAvailability(water_source={'flood_harvest': 200})

# #Climate Variables
# #I thought there would be more, so used a ParameterSet.
# #Climate = ParameterSet(surface_evap_rate=0.4)

# FarmDam_params = ParameterSet(
#     include_farm_dam_capital_costs=False,
#     name='Farm Dam',
#     num_years=30,
#     storage_capacity_ML=200,
#     storage_cost_per_ML=1000,
#     cost_capital=0,
#     pump_vol_ML=0,
#     maintenance_rate=0.005,
#     capture_pump_cost_ratio=0.5,
#     pump_cost_dollar_per_ML=35,
#     ClimateVariables=ParameterSet(surface_evap_rate=0.4),
#     WaterSources=WaterSources(water_source=water_sources)
#     )

# Basin_params = ParameterSet(
#     name='Basin',
#     num_years=30,
#     storage_capacity_ML=200,
#     storage_cost_per_ML=0,
#     cost_capital=0,
#     maintenance_rate=0.1,
#     capture_pump_cost_ratio=0.6,
#     pump_cost_dollar_per_ML=35,
#     ClimateVariables=ParameterSet(surface_evap_rate=0.4),
#     WaterSources=WaterSources(water_source=water_sources)
# )

# ASR_params = ParameterSet(
#     name='ASR',
#     num_years=20,
#     storage_capacity_ML=200,
#     storage_cost_per_ML=0,
#     capital_cost_per_ML_at_02_per_day=700, #TESTING, REMOVE WHEN DONE
#     cost_capital=0,
#     maintenance_rate=0.07,
#     capture_pump_cost_ratio=0.6,
#     pump_cost_dollar_per_ML=35,
#     ClimateVariables=ParameterSet(surface_evap_rate=0.4),
#     WaterSources=WaterSources(water_source=water_sources)
# )

# #Create irrigation strategies

# Flood_params = ParameterSet(
#     name='Flood',
#     irrigation_rate=1,
#     #Irrigation Efficiency
#     #0.76, #From Ticehurst et al. under review, p 6
#     #0.5-0.8, with average of 0.55 according to Smith, NSW DPI agronomist 2012, table of comparative irrigation costs
#     irrigation_efficiency=0.55,
#     lifespan=10,
#     #cost per Ha
#     #2500-3000 Smith, NSW DPI agronomist 2012, table of comparative irrigation costs
#     #set to 0 as Flood irrigation is already built
#     cost_per_Ha=0,
#     #From Smith 2012
#     replacement_cost_per_Ha=2500
# )

# Flood = IrrigationPractice(**Flood_params.getParameters())

# Spray_params = ParameterSet(
#     name='Spray',
#     irrigation_rate=1,
#     #0.8 From Smith, NSW DPI agronomist, table of comparative irrigation costs and from Ticehurst et al. under review, p 6
#     irrigation_efficiency=0.8,
#     lifespan=15,
#     #2000-3000 River, 2500-3500 Bore, Smith, NSW DPI agronomist 2012, table of comparative irrigation costs
#     cost_per_Ha=2500
# )

# Drip_params = ParameterSet(
#     name='Drip',
#     irrigation_rate=1,
#     #0.85 from Smith and from Ticehurst et al. under review, p 6
#     irrigation_efficiency=0.85,
#     lifespan=15,
#     #6000 - 9000 Smith, NSW DPI agronomist 2012, table of comparative irrigation costs
#     cost_per_Ha=6000
# )

# #Create crops
# Cotton_params = ParameterSet(
#     crop_name='Cotton',
#     #price per yield (538) Taken from original code
#     price_per_yield=538,
#     yield_per_Ha=9.5,
#     #water use ML per Ha is 6.004, assumed value based on figure in original code
#     #(7.59 * (Flood.irrigation_efficiency => 0.55) )
#     water_use_ML_per_Ha=4.345, #7.9 (value as found in Arshad et al. 2013) * 0.55 (average flood irrigation efficiency) = 4.345 #6.004 (figure based on 7.9 * 0.76 => national average),
#     #Cotton.water_use_ML_per_Ha = 7.59 #Taken from Montegomery & Bray, Figure 1, p 5
#     #variable cost taken from original code. 153.1 represents pigeon pea, sacrificial crop (uses ~5% of land)
#     variable_cost_per_Ha=2505+153.1
# )

# #WARNING: Dummy values are used here
# Wheat_params = ParameterSet(
# 	crop_name="Wheat",
# 	price_per_yield=100,
# 	yield_per_Ha=10,
# 	required_water_ML_per_Ha=2,
# 	variable_cost_per_Ha=2500
# )

# Cotton = CropInfo.CropInfo(**Cotton_params.getParameters())
# Wheat = CropInfo.CropInfo(**Wheat_params.getParameters())

# print Wheat