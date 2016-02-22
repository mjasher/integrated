from __future__ import division

"""
Farm Model in development

Farm Water Calculator
http://agriculture.vic.gov.au/agriculture/farm-management/soil-and-water/water/farm-water-solutions/farm-water-calculator

NOTES:
Simulating water trading between farmers:
  Generate water saving (WS) curve for each farm
  Generate water deficit (WD) curve for each farm
  Plot WS vs WD between two farms and find 0 (root finding) and you can simulate trades between farms

Each Irrigation system has an assumed head pressure
TODO: Check these head pressures

I am assuming that the pumping cost figures stated reflect water application heads from surface water or a storage.

For groundwater pumping, have to add the depth below pump (THIS IS NOT YET IMPLEMENTED)


mm -> ML/Ha = division by 100
ML -> mm = multiplication by 100
Total ML -> mm = (ML/area) * 100

TODO: Proper values - currently using a mix of possible and dummy values

Efficiency of Irrigation
Vn is amount of water needed by the crop in the root zone (mm/cubic metre)
and Vf is the amount of water reaching the field (mm/cubic metre)
e_i = 100 * (Vn / Vf)

Vf = (water_to_apply[f] / f.area) * 100

if Vf > 0:
	e_i = 100 * (Vn/Vf)
else:
	e_i = 0

print "Application Efficiency"
print e_i

"""

if __name__ == "__main__":

	import datetime

	from integrated.Modules.WaterSources import WaterSources
	import integrated.Modules.Farm.setup_dev as FarmConfig
	from integrated.Modules.Farm.Farms.FarmInfo import FarmInfo
	from integrated.Modules.Farm.Management.Manager import FarmManager
	from integrated.Modules.Farm.WaterStorages.FarmDam import FarmDam
	from integrated.Modules.Farm.Fields.Field import FarmField
	from integrated.Modules.Farm.Fields.Soil import SoilType
	from integrated.Modules.Farm.Crops.CropInfo import CropInfo
	from integrated.Modules.Core.Handlers.FileHandler import FileHandler
	from integrated.Modules.Core.Handlers.BOMHandler import BOMHandler

	TestFarm = FarmInfo(**FarmConfig.BASE_FARM.getParams())

	print "Processing {farm_name}".format(farm_name=TestFarm.name)
	print "--------------------------"

	print "Setting up historical data for Echuca area"
	print "--------------------------"

	# ClimateData = BOMHandler().loadBOMCSVData('test_data/climate/IDCJAC0009_080015_1800/IDCJAC0009_080015_1800_Data.csv', 
	# 	data_cols=['Rainfall amount (millimetres)'],
	# 	date_range=['1950-06-01','1952-06-01'])

	# from integrated.Modules.Climate.ClimateVariables import Climate
	# Climate = Climate(rainfall=ClimateData)
	# del ClimateData #Remove temp dataframe

	#Echuca Data for Development purposes
	#columns=['Date2', 'Rain', 'Evap']
	import pandas as pd

	ClimateData = FileHandler().loadCSV('test_data/climate/Echuca.txt', columns=[0, 7, 9], skiprows=41, delimiter=r'\s*', engine='python') #
	ClimateData.index = pd.to_datetime(ClimateData[ClimateData.columns[0]], format='%Y%m%d')
	ClimateData.columns = ['Date', 'rainfall', 'ET']

	water_sources = [
		WaterSources(name='Surface Water', water_level=2, entitlement=400.3, water_value_per_ML=150, cost_per_ML=75),
		WaterSources(name='Groundwater', water_level=30, entitlement=284.0, water_value_per_ML=150, cost_per_ML=66)
	]

	storages = [FarmDam(**FarmConfig.FarmDam_params.getParams())]
	irrigations = [FarmConfig.PipeAndRiser, FarmConfig.Spray]
	crops = [CropInfo(**cp.getParams()) for crop_name, cp in FarmConfig.crop_params.iteritems()]

	Manager = FarmManager(TestFarm, storages, water_sources, irrigations, crops)

	#DUMMY VALUES
	#See Table 2, Echuca:
	#http://www.g-mwater.com.au/downloads/gmw/Groundwater/Lower_Campaspe_Valley_WSPA/30_Sept_2015-LOWER_CAMPASPE_VALLEY_WSPA_ANNUAL_REPORT_-_2014_15_-_SIGNED.pdf
	Manager.Farm.water_sources['surface_water'] = WaterSources(name='Surface Water', water_level=10, entitlement=300.3, water_value_per_ML=150, cost_per_ML=75)
	Manager.Farm.water_sources['groundwater'] = WaterSources(name='Groundwater', water_level=30, entitlement=284.0, water_value_per_ML=150, cost_per_ML=66)

	Manager.Farm.storages = {'Farm Dam': FarmDam(**FarmConfig.FarmDam_params.getParams())}

	#Rough guess
	#Farmers often do not use the entirety of their water allocations
	#water_entitlement = 2533.5 #MLs
	#usual_water_use = water_entitlement * 0.7 

	#DUMMY VALUE TAKEN FROM
	#http://www.airborneresearch.com.au/Rainfall%20Trends%20on%20the%20Continent%20of%20Australia.pdf
	#Expected Growing Season Rainfall
	expected_rainfall_mm = 790 #790 / 2 #mm, YEARLY / 2

	timestep = datetime.date(year=1951, month=6, day=1)
	end_date = datetime.date(year=1972, month=2, day=20)

	FarmDam = FarmDam(**FarmConfig.FarmDam_params.getParams())

	#Setting up fields for development
	#These represent homogenous areas of soil type and irrigation system
	fields = [
		FarmField(irrigation=FarmConfig.PipeAndRiser, area=40, storage=FarmDam.getCopy(), soil=SoilType(**FarmConfig.Loam_params.getParams())),
		FarmField(irrigation=FarmConfig.Spray, area=40, storage=FarmDam.getCopy(), soil=SoilType(**FarmConfig.Loam_params.getParams())),
		FarmField(irrigation=FarmConfig.PipeAndRiser, area=10, storage=FarmDam.getCopy(), soil=SoilType(**FarmConfig.Clay_loam_params.getParams())),
		FarmField(irrigation=FarmConfig.Spray, area=10, storage=FarmDam.getCopy(), soil=SoilType(**FarmConfig.Clay_loam_params.getParams()))
	]

	print "--- Determine what to plant in each field ---"

	field_results = {}
	original_sw_ent = Manager.Farm.water_sources['surface_water'].entitlement
	original_gw_ent = Manager.Farm.water_sources['groundwater'].entitlement

	total_est_profit = 0
	for Field in fields:

		field_results[Field.name], res = Manager.determineFieldCombinations(Field, expected_rainfall_mm)

		for crop_name in Manager.Farm.crops:

			Crop = Manager.Farm.crops[crop_name]

			total_est_profit += field_results[Field.name][Crop.name]['total_profit']

			#Update water used
			sw = field_results[Field.name][Crop.name]['surface_water']["water_applied"]
			gw = field_results[Field.name][Crop.name]['groundwater']["water_applied"]
			Manager.Farm.water_sources['surface_water'].entitlement = Manager.Farm.water_sources['surface_water'].entitlement - sw
			Manager.Farm.water_sources['groundwater'].entitlement = Manager.Farm.water_sources['groundwater'].entitlement - gw
		#End for
	#End for

	print "Estimated Profit: {p}".format(p=total_est_profit)

	#Reset entitlements
	Manager.Farm.water_sources['surface_water'].entitlement = original_sw_ent
	Manager.Farm.water_sources['groundwater'].entitlement = original_gw_ent

	#Add fields to farm
	for field_name in field_results:
		for crop_name in field_results[field_name]:
			if 'fields' in field_results[field_name][crop_name]:
				Manager.Farm.fields.extend(field_results[field_name][crop_name]['fields'])
			#End if

		#End for
	#End for

	print "---------------------"

	# import sys
	# sys.exit()

	#####################################

	total_effective_rainfall = 0.0
	total_water_applied = 0.0
	pumping_costs = 0.0

	step = 14 #days for each timestep
	for ts in xrange(step, 200, step):

		#Assume first time step is week starting June 1
		loop_timestep = timestep + datetime.timedelta(days=ts)

		#Start time step
		print "--- Start time step {i} - {t} ---\n".format(i=(timestep + datetime.timedelta(days=ts-step)), t=loop_timestep)

		timestep_ETo = ClimateData.ET[ (ClimateData.index >= (str(timestep + datetime.timedelta(days=ts-step)))) & (ClimateData.index < str(loop_timestep))].sum()

		timestep_rainfall = ClimateData.rainfall[ (ClimateData.index >= (str(timestep + datetime.timedelta(days=ts-step)))) & (ClimateData.index < str(loop_timestep))][:]

		#Sum of rainfall that occured in this timestep
		total_timestep_rainfall = timestep_rainfall.sum()

		#Calculate how much water to apply, and send the water out
		water_to_apply = Manager.calcWaterApplication()

		for Field in Manager.Farm.fields:

			#Testing dryland
			# water_to_apply[Field] = 0.0

			#Check if crop is ready for harvest (if applicable)
			if Field.Crop.harvest(loop_timestep) is True:
				Field.Crop.planted = False

			if Field.Crop.planted is False:
				continue

			###
			# TODO: Optimise which water source to get water from
			#		Update fuel costs
			#		Check that pumping costs are done correctly
			#		Check Flow rate calculation. Changing from Gallons per minute to Lps doesn't seem to have much of an effect
			###
			water_source_name = 'surface_water'

			#Effective Rainfall = Rainfall - 5mm
			effective_rainfall = (total_timestep_rainfall - 5.0) if (total_timestep_rainfall - 5.0) > 0.0 else 0.0
			effective_rainfall = (effective_rainfall / 100) * Field.area #total input over field area in ML

			flow_rate_Lps = Field.calcFlowRate() #Field.pump_operation_hours, Field.pump_operation_days, Crop=Field.Crop
   			pumping_cost_per_ML = Manager.Farm.water_sources[water_source_name].calcPumpingCostsPerML(flow_rate_Lps=flow_rate_Lps, head_pressure=Field.Irrigation.head_pressure)

   			# timestep_flow_rate = flow_rate_Lps
			timestep_pumping_cost = round(water_to_apply[Field] * pumping_cost_per_ML, 2)

			# print pumping_cost_per_ML
			# print Field.calcFlowDurationInDays(water_to_apply[Field])
			# print water_to_apply[Field]
			# print "{0:.2f}".format(timestep_pumping_cost)
			# print "-=-=-=-=+++++++++++++++"

			water_input = effective_rainfall + water_to_apply[Field] #ML total

			ET_c = (timestep_ETo * Field.Crop.getCurrentStageCoef(loop_timestep))

			print "  SWD Before Application: {c}mm".format(c=Field.c_swd)
			recharge = Field.updateCumulativeSWD(ET_c, water_input)
			print "  SWD After Application: {c}mm".format(c=Field.c_swd)
			print "  Area: {a}".format(a=Field.area)
			print "  Soil: {s}".format(s=Field.Soil.name)
			print "  TAW: {s}".format(s=Field.Soil.current_TAW_mm)
			print "  RAW: {s}".format(s=Field.Soil.calcRAW(fraction=Field.Crop.depletion_fraction))
			print "  ET_c: {etc}mm, {t}ML, {avg} ML/Ha".format(etc=((ET_c/Field.area) * 100), t=ET_c, avg=ET_c/Field.area)
			print "  Total Rain: {r}mm, {t}ML, {avg}ML/Ha".format(r=total_timestep_rainfall, t=(total_timestep_rainfall/100)*Field.area, avg=(total_timestep_rainfall/100) )
			print "  Effective Rain: {r}mm, {avg} ML/Ha".format(r=(effective_rainfall/Field.area)*100, avg=effective_rainfall/Field.area)
			print "  Applied Irrigation Water: {i}mm, {t}ML, {avg} ML/Ha".format(i= (water_to_apply[Field]/Field.area)*100, t=water_to_apply[Field], avg=water_to_apply[Field]/Field.area)
			print "  Total Water Input: {tw} ML/Ha".format(tw=water_input/Field.area)
			print "  Flow Rate: {fr} Lps".format(fr=flow_rate_Lps)
			print "  Pumping Cost per ML: {pc}".format(pc=pumping_cost_per_ML)
			print "  Total Timestep Pumping Cost: ${pc}".format(pc=timestep_pumping_cost)
			print "  Total Pumping Cost: ${pc}".format(pc=pumping_costs+timestep_pumping_cost)
			print "  NID: {nid}".format(nid=Field.calcNetIrrigationDepth(Field.Crop.root_depth_m, Field.Crop.depletion_fraction))
			print "  Gross Water Input: {wi}mm, {avg} ML/Ha".format(wi=(water_input/Field.area)*100, t=water_input, avg=water_input/Field.area)
			print "  Recharge: {r}mm, {t}ML, {avg} ML/Ha".format(r=(recharge*100), t=recharge*Field.area, avg=recharge)

			total_effective_rainfall += total_timestep_rainfall
			total_water_applied = total_water_applied + water_input
			Field.water_applied = Field.water_applied + water_to_apply[Field]

			print "  Total Irrigation Water Applied: {aw}ML".format(aw=Field.water_applied)

			pumping_costs += timestep_pumping_cost

		#End for

		#Print status of Fields
		print "---------------"
		# for field in Manager.Farm.fields:
		# 	print field.status()

		#Do some other stuff... like look after the cows

		#End of Season

		#Harvest crops

		#Determine which fields to harvest from
		# harvest_fields = Manager.getHarvestableCrops()

		# harvest = Manager.harvestCrops(harvest_fields)

		# gross_profit = 0
		# for f in harvest_fields:
		# 	gross_profit = gross_profit + (harvest[f.crop.name] * f.crop.price_per_yield)[0]
		# #End for

		# print "Gross Harvest Value: ${g}".format(g=gross_profit)

		# TestFarm.net_profit = TestFarm.net_profit + gross_profit

		#Calculate harvest value

		#End of timestep, loop back
		print "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n"

		if loop_timestep > end_date:
			break
		#End if
		
	#End of scenario range

	print "Total Irrigation Water Applied during season: {wa}, {avg} ML/Ha".format(wa=total_water_applied, avg=float(total_water_applied)/float(Manager.Farm.getFarmArea()))

	storage_name, Storage = Manager.Farm.getStorageInUse()
	storage_cost = Storage.calcStorageCosts(Storage.storage_capacity_ML)
	storage_maintenance_cost = Storage.calcMaintenanceCosts(Storage.storage_capacity_ML)

	total_area = 0
	total_income = 0
	crop_costs = 0
	for f in Manager.Farm.fields:

		print f.name

		raw = Field.Soil.calcRAW(fraction=Field.Crop.depletion_fraction)
		#taw = Field.Soil.TAW_mm

		avg_crop_ET = f.Crop.planting_info.mean()[0]

		if f.water_applied == 0:
			crop_yield = Manager.calcPotentialCropYield(raw, total_effective_rainfall, avg_crop_ET, Field.Crop.wue_coef)
		else:
			crop_yield = Manager.calcPotentialCropYield(raw, (f.water_applied+total_effective_rainfall)*2, avg_crop_ET, Field.Crop.wue_coef)

		print f.water_applied, total_effective_rainfall, total_water_applied

		try:
			WUE = crop_yield / f.water_applied
			WUE_kg_ha_mm = (crop_yield / f.area) / (f.water_applied / f.area)
		except ZeroDivisionError:
			WUE = crop_yield / 1
			WUE_kg_ha_mm = (crop_yield / f.area) / 1
		
		print "    Area (Ha): {a}".format(a=f.area)
		print "    Soil: {s}".format(s=f.Soil.name)
		print "    Yield (t/Ha): {cy}".format(cy=crop_yield/f.area)
		print "    Total Water Applied: {n}".format(n=f.water_applied)
		print "    Water Applied (ML/Ha): {wa}".format(wa=f.water_applied/f.area)
		print "    Total Effective Rain: {er}".format(er=total_effective_rainfall)
		print "    WUE: {w}".format(w=WUE)
		print "    Gross Income: {gi}".format(gi=f.Crop.price_per_yield*crop_yield)
		# print "    Pumping Costs: {pc}".format(pc=pumping_costs)
		print "    Crop Costs: {cc}".format(cc=f.Crop.variable_cost_per_Ha*f.area)

		crop_costs += (f.Crop.variable_cost_per_Ha * f.area)

		total_income += (f.Crop.price_per_yield*crop_yield)
		total_area = total_area + f.area
	#End for

	#calc storage costs for field
	storage_cost = storage_maintenance_cost #storage_cost+

	#crop cost for field

	total_income = total_income - (storage_cost + pumping_costs + crop_costs) #storage_cost


	print "Total Income: ${inc}".format(inc=total_income)
	print "Costs: {pc} + {sc}".format(pc=pumping_costs, sc=storage_cost)
	print "Annualised Capital Return: {acr}".format(acr=Manager.Farm.annualizeCapital(total_income) )
	print "Annualised Costs: {ac}".format(ac=Manager.Farm.annualizeCapital(pumping_costs+storage_cost))

	print "Total Area of Final Season: {area} Ha".format(area=total_area)

	


