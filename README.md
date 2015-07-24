# integrated
Integrated surface water, groundwater, farm process, water policy, ecological model.

MODFLOW_GROUNDWATER_MODEL
-------------------------
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
* heads (day, row, col, lay)
* flows (day, row, col, lay, side)


SURFACE_WATER_MODEL
-------------------------
Inputs
* rainfall (day, location, volume)
* temperature (day, location, temperature)
* humidity (day, location, humidity)
* boundary inflow (day, river_stage, volume)

Outputs
* river_stages (day, row, col, lay, stage_height, conductance, river_bottom)


FARM_MODEL
-------------------------
Inputs
* crop_prices (year, price)
* water_allocation (year, allocation)
* farm_area
* profit_margins

Outputs
* farm_profit (year)


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
