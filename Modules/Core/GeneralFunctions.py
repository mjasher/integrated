from __future__ import division
import pandas as pd
import paths

"""
Methods that are non-specific to any module.
"""

def calcCapitalCostPerYear(capital, discount_rate, num_years):

    """
    Calculates capital value per year over a given number of years

    :param capital: Amount of money in dollars ($)
    :param discount_rate: The percentage to discount future value to get present-day value; Arshad et al. (2013) used 7%
    :param num_years: Number of years for the scenario
    :returns: Annualised capital cost discounted to present day value 
    :return type: numeric
    
    """

    annuity_factor = (1 - 1/(1 + discount_rate)**num_years)/discount_rate

    return (capital/annuity_factor)

#End calcCapitalCostPerYear()


#Optimization helper methods
def packParams(params, name, defaults_list=[], bounds_list=[]):

    """
    Pack parameters into a series of values to pass to Objective Function
    
    NOTE: Unpacking order should follow packing order
    """

    for index, row in params.iterrows():
        #arg_list[name][row_id] = row.parameter
        defaults_list.append(row['best_guess'])
        bounds_list.append( (row['min_bound'], row['max_bound']) )
    #End for

    return defaults_list, bounds_list
#End packParams()

def unpackParams(start, x, parameters):

    """
    Parameter x passed to objective function is a series of values of arbitrary length
    
    This method reconstructs a dictionary map of {parameter_name: value}
    
    NOTE: Unpacking order should follow packing order
    """

    params = {}
    position = start
    for row_id, row in parameters.iterrows():
        pos = position + row_id
        params[row.parameter] = x[pos]
    #End for

    position = position + row_id + 1

    #Return position of x this function got to
    return params, position
#End unpackParams()

def importParamsFromDF(df, col='best_guess'):

    """
    Extract parameter values from a given DataFrame

    :returns: Dict
    """

    params = {}
    for row_id, row in df.iterrows():
        params[row.parameter] = row[col]
    #End for

    return params
#End importParamsFromDF()

def importSpecificRangesFromFiles(store, irrigation, crop):

    """
    Import best guess parameters, local PoCs, Global PoCs, and breakeven points at best guess
    
    TODO: Clean up. This is incredibly messy.
    """

    import pandas as pd

    Data = {}

    #Folder paths
    path_to_ranges = paths.path_to_ranges
    storage_ranges = paths.storage_ranges
    irrigation_ranges = paths.irrigation_ranges
    crop_ranges = paths.crop_ranges

    output_path = paths.output_path

    farm_id = store+"_"+irrigation+"_"+crop

    ### Import Best Guess

    #Import ranges as variables
    FarmDam_vars, BasinStorage_vars, ASRStorage_vars = importStorageRanges()

    #Irrigation ranges
    Flood_vars, Spray_vars, Drip_vars = importIrrigationRanges()

    #Crop ranges
    Cotton_vars = importCropRanges()

    Data['best_guess'] = {}
    Data['best_guess']['FarmDam'] = FarmDam_vars
    Data['best_guess']['BasinStorage'] = BasinStorage_vars
    Data['best_guess']['ASRStorage'] = ASRStorage_vars

    Data['best_guess']['Flood'] = Flood_vars
    Data['best_guess']['Spray'] = Spray_vars
    Data['best_guess']['Drip'] = Drip_vars

    Data['best_guess']['Cotton'] = Cotton_vars

    ### Import local optimised variables (individual variables close to best guess) ###
    try:
        store_path = output_path+"local/"+farm_id+"/storages/"
        store_opt = pd.read_csv(store_path+store+".csv", skiprows=0, skipinitialspace=True, index_col=0, header=0)

        #Irrigation ranges
        irrig_path = output_path+"local/"+farm_id+"/irrigations/"
        irrig_opt = pd.read_csv(irrig_path+irrigation+".csv", skiprows=0, skipinitialspace=True, index_col=0, header=0)

        #Crop ranges
        Cotton_opt = pd.read_csv(output_path+"local/"+farm_id+"/crops/cotton.csv", skiprows=0, skipinitialspace=True, index_col=0, header=0)

        Data['local'] = {}
        Data['local'][store] = store_opt
        Data['local'][irrigation] = irrig_opt
        Data['local']['Cotton'] = Cotton_opt
    except Exception, e:
        print "Error occured loading local PoCs"
        print e

    #### Breakeven Points ####
    try:
        store_path = output_path+"breakeven/"+farm_id+"/storages/"
        store_opt = pd.read_csv(store_path+store+".csv", skiprows=0, skipinitialspace=True, index_col=0, header=0)

        #Irrigation ranges
        irrig_path = output_path+"breakeven/"+farm_id+"/irrigations/"
        irrig_opt = pd.read_csv(irrig_path+irrigation+".csv", skiprows=0, skipinitialspace=True, index_col=0, header=0)

        #Crop ranges
        Cotton_opt = pd.read_csv(output_path+"breakeven/"+farm_id+"/crops/cotton.csv", skiprows=0, skipinitialspace=True, index_col=0, header=0)

        Data['breakeven'] = {}
        Data['breakeven'][store] = store_opt
        Data['breakeven'][irrigation] = irrig_opt
        Data['breakeven']['Cotton'] = Cotton_opt
    except Exception, e:
        print "Breakeven folder not found"
        print e

    try:
        ### Import Global optimised variables (close to best guess) ###
        store_path = output_path+"closest/"+farm_id+"_(Points_of_Concern)"+"/storages/"
        store_closest = pd.read_csv(store_path+store+".csv", skiprows=0, skipinitialspace=True, index_col=0, header=0)

        #Irrigation ranges
        irrig_path = output_path+"closest/"+farm_id+"_(Points_of_Concern)"+"/irrigations/"
        irrig_closest = pd.read_csv(irrig_path+irrigation+".csv", skiprows=0, skipinitialspace=True, index_col=0, header=0)

        #Crop ranges
        Cotton_closest = pd.read_csv(output_path+"closest/"+farm_id+"_(Points_of_Concern)"+"/crops/cotton.csv", skiprows=0, skipinitialspace=True, index_col=0, header=0)

        Data['closest'] = {}
        Data['closest'][store] = store_closest
        Data['closest'][irrigation] = irrig_closest
        Data['closest']['Cotton'] = Cotton_closest
    except Exception, e:
        print "Error loading globally optimised variables (closest to best guess)"
        print e
    #End

    return Data

#End importDataFromFiles()

def importStorageRanges():

    """
    Import Water Storage value ranges from data paths as set in paths.py
    
    TODO: Clean up or remove
    """
    
    import paths

    storage_ranges = paths.storage_ranges

    #Import ranges as variables
    #Using FileHandler, seems to work
    import Common.FileHandler
    Importer = Common.FileHandler.FileHandler()
    storage_files = Importer.importFiles(storage_ranges)

    FarmDam_vars = storage_files['farmdam']
    BasinStorage_vars = storage_files['basin']
    ASRStorage_vars = storage_files['ASR']

    return FarmDam_vars, BasinStorage_vars, ASRStorage_vars
#End importStorageRanges()

def importIrrigationRanges():

    """
    Import Irrigation value ranges from data paths as set in paths.py
    
    TODO: Clean up or remove
    """

    import paths
    
    irrigation_ranges = paths.irrigation_ranges

    import Common.FileHandler
    Importer = Common.FileHandler.FileHandler()
    irrigation_files = Importer.importFiles(irrigation_ranges)

    Flood_vars = irrigation_files['flood']
    Spray_vars = irrigation_files['spray']
    Drip_vars = irrigation_files['drip']

    return Flood_vars, Spray_vars, Drip_vars

#End importIrrigationData()

def importCropRanges():

    """
    Import Crop value ranges from data paths as set in paths.py
    
    TODO: Clean up or remove
    """
    
    import paths

    crop_ranges = paths.crop_ranges

    import Common.FileHandler
    Importer = Common.FileHandler.FileHandler()
    crop_files = Importer.importFiles(crop_ranges)

    #Cotton_vars = pd.read_csv(crop_ranges+"cotton.csv", skiprows=1, skipinitialspace=True)
    Cotton_vars = crop_files['cotton']

    return Cotton_vars
#End importCropData()

def importRanges(component, component_type=None):

    """
    Import range data for a component (Storage, irrigation, crop, etc.) and component_type (Farm Dam, Spray Irrigation, or crop type)
    """

    #@TODO: Scan folder for folder with same name as component
    #       Then import file with same name as component type
    #       Replace use of import_____Ranges() with this one

    pass

    #import paths

#End importRanges()


def setupParamsForOptScenario(ranges, names, case='best_guess', attrib='best_guess'):

    """
    Set up Farm Component parameters for scenario.
    
    WARNING: Flood harvest is hardcoded (200ML)
    
    TODO: Move to CSV files
    """

    store_vars = ranges[case][names['store_name']]
    irrig_vars = ranges[case][names['irrig_name']]
    crop_vars = ranges[case][names['crop_name']]

    store_params = importParamsFromDF(store_vars, attrib)

    #Set up extra attributes
    store_params['name'] = names['store_name']

    from ParameterSet import ParameterSet
    import WaterAvailability
    store_params['WaterSources'] = WaterAvailability.WaterAvailability(water_source={'flood_harvest': 200})

    store_params['ClimateVariables'] = ParameterSet(surface_evap_rate=store_params['surface_evap_rate'])

    irrig_params = importParamsFromDF(irrig_vars, attrib)
    irrig_params['name'] = names['irrig_name']
    irrig_params['irrigation_rate'] = 1

    crop_params = importParamsFromDF(crop_vars, attrib)
    crop_params['crop_name'] = names['crop_name']

    bounds = {}
    bounds[names['store_name']] = getBounds(store_vars)
    bounds[names['irrig_name']] = getBounds(irrig_vars)
    bounds[names['irrig_name']]['irrigation_rate'] = (1, 1)
    bounds[names['crop_name']] = getBounds(crop_vars)

    return store_params, irrig_params, crop_params, bounds
#End setupParamsForOptScenario()

def getBounds(params, bounds_list={}):

    """
    
    :returns: Value range bounds as found in DataFrame parsed from csv files
    """

    for index, row in params.iterrows():
        bounds_list[row.parameter] = (row['min_bound'], row['max_bound'])
    #End for

    return bounds_list
#End getBounds()