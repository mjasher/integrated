from __future__ import division
"""
Farm Model in development

NOTES:
Simulating water trading between farmers:
  Generate water saving (WS) curve for each farm
  Generate water deficit (WD) curve for each farm
  Plot WS vs WD between two farms and find 0 (root finding) and you can simulate trades between farms


mm -> ML/Ha = division by 100
ML -> mm = multiplication by 100
Total ML -> mm = (ML/area) * 100

TODO: DOUBLE CHECK CALCULATIONS; THEY ARE COMPLETELY OFF 

"""

if __name__ == "__main__":

	import datetime

	import integrated.Modules.Farm.setup_dev as FarmConfig
	from integrated.Modules.Farm.Farms.FarmInfo import FarmInfo
	from integrated.Modules.Farm.Farms.Management import FarmManager
	from integrated.Modules.Farm.Fields.Field import FarmField
	from integrated.Modules.Farm.Fields.Soil import SoilType
	from integrated.Modules.Farm.Crops.CropInfo import CropInfo
	from integrated.Modules.Core.Handlers.FileHandler import FileHandler
	from integrated.Modules.Core.Handlers.BOMHandler import BOMHandler

	#TestFarm = FarmInfo(**FarmConfig.BASE_FARM.__dict__)
	TestFarm = FarmInfo(**FarmConfig.BASE_FARM.getParams())

	print "Processing {farm_name}".format(farm_name=TestFarm.name)
	print "--------------------------"

	print "Setting up historical data for Echuca region"
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

	#from integrated.Modules.Climate.ClimateVariables import Climate
	#Climate = Climate(index=ClimateData.index, rainfall=ClimateData[ClimateData.columns[1]], ET=ClimateData[ClimateData.columns[2]])
	#del ClimateData #Remove temp dataframe

	Manager = FarmManager(TestFarm)

	#TODO: TO BE IMPLEMENTED
	#Manager.determineFieldSize(fields)

	#DUMMY VALUES
	water_entitlement = 1633.5 #MLs

	#Rough guess
	#Farmers often do not use the entirety of their water allocations
	usual_water_use = water_entitlement * 0.7 

	#DUMMY VALUE TAKEN FROM
	#http://www.airborneresearch.com.au/Rainfall%20Trends%20on%20the%20Continent%20of%20Australia.pdf
	#EXPECTED SEASONAL RAINFALL
	expected_rainfall = 790 #mm

	timestep = datetime.date(year=1951, month=6, day=1)

	area_alloc, remaining_area = Manager.plantCrops(initial_area=250.0, soils=[SoilType(**FarmConfig.Light_clay_params.getParams()), SoilType(**FarmConfig.Loam_params.getParams())], timestep=timestep)

	#area_allocation = Manager.determineCropAreaToGrow(initial_area=600.0, soil=[SoilType(**FarmConfig.Light_clay_params.getParams())])

	#Estimate crop yields for farmer decision
	#This happens each season
	for field in Manager.Farm.fields:

		for crop in Manager.Farm.crops:
			crop_info = Manager.Farm.crops[crop]

			RAW_mm = field.soil.calcRAW(fraction=crop_info.depletion_fraction) #Per cubic metre

			print "Crop: {c}".format(c=crop_info.name)

			rainfall_ML_Ha = expected_rainfall / 100
			RAW_ML_Ha = (RAW_mm/100) #RAW in mm per Hectare / 100 = RAW in ML per Ha

			#print field.irrigation.irrigation_efficiency

			#Convert to sum for area of field in Ha
			est_yield = Manager.calcPotentialCropYield(rainfall_ML_Ha*field.area, ( (RAW_ML_Ha*field.area)+crop_info.water_use_ML_per_Ha)*field.area, crop_info.et_coef, crop_info.wue_coef)

			print "Field Area: {fa}".format(fa=field.area)
			print "Estimated Yield: {n} kg/Ha".format(n=est_yield)
			print "Estimated Value: ${v}".format(v=est_yield*crop_info.price_per_yield)
			print "Soil: {s}".format(s=field.soil.name)
			#print "Readily Available Water in Field: {raw}ML/Ha".format(raw=RAW_ML_Ha)
			print "Water Use: {wu} ML/Ha".format(wu=crop_info.water_use_ML_per_Ha)
			print "--------------------"
		#End for
	#End for

	total_water_applied = 0.0

	step = 14 #days for each timestep
	for ts in xrange(step, 365, step):

		#Assume first time step is week starting June 1
		loop_timestep = timestep + datetime.timedelta(days=ts)

		#Start time step
		print "--- Start time step {i} - {t} ---\n".format(i=(timestep + datetime.timedelta(days=ts-step)), t=loop_timestep)

		timestep_ETo = ClimateData.ET[ (ClimateData.index >= (str(timestep + datetime.timedelta(days=ts-step)))) & (ClimateData.index < str(loop_timestep))].sum()

		timestep_rainfall = ClimateData.rainfall[ (ClimateData.index >= (str(timestep + datetime.timedelta(days=ts-step)))) & (ClimateData.index < str(loop_timestep))][:]

		#Sum of rainfall that occured in this timestep
		total_timestep_rainfall = timestep_rainfall.sum()

		#timestep_precipitation = {f: total_timestep_rainfall for f in Manager.Farm.fields}

		#Calculate how much water to apply, and send the water out
		water_to_apply = Manager.calcWaterApplication()

		for f in Manager.Farm.fields:

			print f.name

			#Effective Rainfall = Rainfall - 5mm
			effective_rainfall = (total_timestep_rainfall - 5.0) if (total_timestep_rainfall - 5.0) > 0.0 else 0.0
			effective_rainfall = (effective_rainfall / 100) * f.area

			water_input = effective_rainfall + water_to_apply[f] #ML total

			ET_c = (timestep_ETo * f.crop.getCurrentStageCoef(loop_timestep))

			#ETc = ( water_input * f.irrigation.irrigation_efficiency) #f.crop.getCurrentStageCoef(loop_timestep)

			# CWU, recharge = [f.simpleCropWaterUse(water_input).get(k) for k in ['cwu','recharge']]
			# print water_input, CWU, recharge

			# Vn = Manager.calcNetIrrigationDepth(f)

			#Efficiency of Irrigation
			#Vn is amount of water needed by the crop in the root zone (mm/cubic metre)
			#and Vf is the amount of water reaching the field (mm/cubic metre)
			#e_i = 100 * (Vn / Vf)

			# Vf = (water_to_apply[f] / f.area) * 100

			# print Vn
			# print Vf

			# if Vf > 0:
			# 	e_i = 100 * (Vn/Vf)
			# else:
			# 	e_i = 0

			# print "Application Efficiency"
			# print e_i

			print "  SWD Before Application: {c}mm".format(c=f.c_swd)
			recharge = f.updateCumulativeSWD(loop_timestep, ET_c, water_input)
			print "  SWD After Application: {c}mm".format(c=f.c_swd)
			print "  Area: {a}".format(a=f.area)
			print "  Soil: {s}".format(s=f.soil.name)
			print "  TAW: {s}".format(s=field.soil.current_TAW_mm)
			print "  RAW: {s}".format(s=field.soil.calcRAW(fraction=f.crop.depletion_fraction))
			print "  ET_c: {etc}mm, {t}ML, {avg} ML/Ha".format(etc=((ET_c/f.area) * 100), t=ET_c, avg=ET_c/f.area)
			print "  Total Rain: {r}mm, {t}ML, {avg}ML/Ha".format(r=total_timestep_rainfall, t=(total_timestep_rainfall/100)*f.area, avg=(total_timestep_rainfall/100) )
			print "  Effective Rain: {r}mm, {avg} ML/Ha".format(r=(effective_rainfall/f.area)*100, avg=effective_rainfall/f.area)
			print "  Irrigation: {i}mm, {t}ML, {avg} ML/Ha".format(i= (water_to_apply[f]/f.area)*100, t=water_to_apply[f], avg=water_to_apply[f]/f.area)
			print "  NID: {nid}".format(nid=Manager.calcNetIrrigationDepth(f))
			print "  Gross Water Input: {wi}mm, {avg} ML/Ha".format(wi=(water_input/f.area)*100, t=water_input, avg=water_input/f.area)
			print "  Recharge: {r}mm, {t}ML, {avg} ML/Ha".format(r=(recharge*100), t=recharge*f.area, avg=recharge)

			total_water_applied = total_water_applied + water_input

			f.water_applied = f.water_applied + water_to_apply[f]

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

		
	#End of scenario range

	print "Total Irrigation Water Applied during season: {wa}, {avg} ML/Ha".format(wa=total_water_applied, avg=float(total_water_applied)/float(Manager.Farm.getFarmArea()))
	
	for f in Manager.Farm.fields:

		print f.name
		
		crop_yield = f.harvest()

		try:
			WUE = crop_yield / f.water_applied
		except ZeroDivisionError:
			WUE = crop_yield / 1
		
		print "  Area (Ha): {a}".format(a=f.area)
		print "  Soil: {s}".format(s=f.soil.name)
		print "  Yield (t/Ha): {cy}".format(cy=crop_yield/f.area)
		print "  Total Water Applied: {n}".format(n=f.water_applied)
		print "  Water Applied (ML/Ha): {wa}".format(wa=f.water_applied/f.area)
		print "  WUE: {w}".format(w=WUE)
		print "  Gross Income: {gi}".format(gi=f.crop.price_per_yield*crop_yield)
	#End for


