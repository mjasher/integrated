import datetime
import Modules
import Setup.FarmModel_setup as FarmConfig

from Modules.Farm.Farms.FarmInfo import FarmInfo
from Modules.Farm.Farms.Management import FarmManager
from Modules.Farm.Fields.Field import FarmField
from Modules.Farm.Fields.Soil import SoilType

"""
Main script in development
This is the "Master" script that calls all other modules and handles their interactions
"""

if __name__ == "__main__":

	print "Running Farm Module!"

	TestFarm = FarmInfo(**FarmConfig.BASE_FARM.getParams())

	print "Processing {farm_name}".format(farm_name=TestFarm.name)
	print "--------------------------"

	Manager = FarmManager(TestFarm)

	#TODO: TO BE IMPLEMENTED
	#Manager.determineFieldSize(fields)

	#area_allocation = Manager.determineCropAreaToGrow(initial_area=500.0, soils=[SoilType(**FarmConfig.Light_clay_params.getParams())])

	timestep = datetime.date(year=1950, month=6, day=1)

	area_alloc, remaining_area = Manager.plantCrops(initial_area=500.0, soils=[SoilType(**FarmConfig.Light_clay_params.getParams())], timestep=timestep)

	step = 14
	for ts in xrange(0, 365, step):

		#Assume first time step is week starting June 1
		loop_timestep = timestep + datetime.timedelta(days=ts)

		#Start time step
		print "--- Start time step {t} ---\n".format(t=loop_timestep)

		#TODO:
		#Decide to deficit irrigate?

		#Calculate how much water to apply, and send the water out
		water_to_apply = Manager.calcWaterApplication()

		recharge = Manager.applyWater(water_to_apply)

		#print "Applied water: "
		for w in water_to_apply:
			if water_to_apply[w] != 0.0:
				print "{c}: {a}".format(c=w.crop.name, a=water_to_apply[w])
			#End if
		#End for

		print "Recharge: {r}".format(r=recharge)

		#Calculate Cumulative Soil Water Deficit
		Manager.calcCumulativeSWD(loop_timestep, 7.5*step, water_to_apply)

		#print "{r} ML of water went to recharge".format(r=recharge)

		#Do some other stuff... like look after the cows

		TestFarm.applyCropLosses()

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

	print "Farm Profit: ${profit}".format(profit=TestFarm.net_profit)
	#Calculate net profit
