#http://agriculture.vic.gov.au/agriculture/horticulture/vegetables/vegetable-growing-and-management/estimating-vegetable-crop-water-use
# Total available water in mm per metre of soil depth
# Texture Class Range   Average
# Sand  30 - 65 49
# Sandy Loam    90 - 123    106
# Loam  155 - 172   164
# Light Clay Loam   172 - 180   172
# Clay Loam 155 - 172   164
# Heavy Clay Loam   137 -155    147


#Moisture Balance sheet for scheduling irrigation
#Let's test this with tomatoes

#Crop   Initial Development Mid season  Late    At harvest
#Tomato 0.4 - 0.5   0.7 - 0.8   1.05 - 1.25 0.8 - 0.95  0.6 - 0.65

from sympy import symbols

ETc = 5 #mm / day

#Define mathematical and SI units of measurement
m = symbols('m')
mm = m / 1000.0
Ha = 100.0 * 100.0 * m


root_depth_m = (0.5, 1.5)
depletion_fraction_p = (0.4, 0.5)

#p = p (table 4) + 0.04 (5 - ETc)

p = 0.4
TAW = 180 * mm
RAW = p * TAW

net_irrigation_depth = (0.55 * m) * RAW

"""
Calculation for each timestep
  Need: 
    ET_0 in timestep, in mm
    ETc in timestep, in mm
    Rainfall that occured in timestep, in mm

  ET_0 * ETc = Crop Water Use

  Effective Rainfall (in mm) = Rainfall - ETc

  Net Irrigation Application = amount of water applied (in mm)

  Cumulative Soil Water Deficit = (Effective Rainfall + Net Irrigation Application) - Crop Water Use

  Irrigation water should be applied when Cumulative Soil Water Deficit reaches net irrigation depth

  see Table 4 at
  http://agriculture.vic.gov.au/agriculture/horticulture/vegetables/vegetable-growing-and-management/estimating-vegetable-crop-water-use

  To calculate effective rainfall, during spring, summer and autumn periods, subtract 5 mm from each of the daily rainfall totals. 
  Assume rainfalls of 5 mm or less to be non-significant (zero). 
  In winter, all the rainfall is assumed to be effective.

  1mm = 1L per m^2
    = 10,000L per Hectare

So we have irrigation efficiency of 0.55 percent (made up number for example purposes)

  Irrigation water applied = 6ML

  ETc during irrigation events is assumed to be
    Irrigation Water * Irrigation Efficiency

  Therefore: 
    ETc = 6 * 0.55 
         = 3.3

  Cumulative Soil Water Deficit = (0.0 + 6.0) - 3.3
    = 2.7ML (convert this to mm?)

"""
