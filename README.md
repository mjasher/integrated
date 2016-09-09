# DEPRECATED

# integrated
Integrated surface water, groundwater, farm process, crop yield, water policy, ecological model.

GROUNDWATER_MODEL
-------------------------
River interaction, MAR, diffuse recharge and evapotranspiration, pumping.

Inputs (by MODFLOW package)
* BAS
	- domain (row, col, lay)
	- initial_head (row, col, lay)
* DIS
* RIV
	- river_stages (day, row, col, lay, stage_height, conductance, river_bottom)
* WEL
	- wells (day, row, col, lay, flow)
* RCH
	- recharge (day, row, col, lay)
* FLOW (eg. LPF)
	- hydraulic_conductivity (row, col, lay)
	- storage (row, col, lay)
* SOLVER (eg. SIP)

Outputs
* storage (day, row, col, lay)
* heads (day, row, col, lay)
* flows (day, row, col, lay, side)


SURFACE_WATER_MODEL
-------------------------
Routing through rivers, tributaries, canals.

Inputs
* rainfall (day, location, volume)
* temperature (day, location, temperature)
* humidity (day, location, humidity)
* boundary inflows and discharges (day, river_stage, volume)
	- inflows from dam, canals
	- discharge downstream
	- diversions, extractions 
Outputs
* river_stages (day, row, col, lay, stage_height, conductance, river_bottom)


FARM_DECISION_MODEL
-------------------------
Crop, irrigation, investment choice.

Inputs
* crop_prices (year)
* water_allocation (year ?)
* farm_area
* crop_costs
* 
* climate

Outputs
* farm_profit (year)
* water_use (day, type)


CROP_MODEL
-------------------------
Crop growth and water demand.

Inputs
* crop_type
* water (day)

Outputs
* yield (year)


ECOLOGICAL_MODEL
-------------------------
Inputs
* river_stages (day, row, col, lay, stage_height, conductance, river_bottom)
* heads (day, row, col, lay)

Outputs
* ecological_index (day, row, col, lay)


INTEGRATED_MODEL
-------------------------
Inputs
* rainfall_driver (day, volume)
* temperature_driver (day, temperature)
* crop_prices (year, price)

Outputs
* ecological_index_average
* farm_profit_average



References
=========================
[CATCHCROP model] (http://www.sciencedirect.com/science/article/pii/S1364815201000743)
[MODFLOW Farm Process](http://water.usgs.gov/nrp/gwsoftware/mf2005_fmp/mf2005_fmp.html)
[Integrated Decision Making for Reservoir, Irrigation, and Crop Management]
[Integrating Irrigation Water Demand, Supply, and Delivery Management in a Stochastic Environment]
[A dynamic model of irrigation and land-use choice: application to the Beauce aquifer in France]
