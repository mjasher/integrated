#flow_dev.py

if __name__ == '__main__':

    #import os
    #os.chdir('C:\\UserData\\fub\\work09\\MDB')
    from integrated.Modules.Ecology.FlowSuitability import FlowSuitability

    from integrated.Modules.Core.Handlers.FileHandler import FileHandler

    FileHandle = FileHandler()

    #Paths to files
    dev_data_path = "Integrated/Modules/Ecology/Inputs"
    #dev_data_path = "Inputs"

    # Read in flow data
    scenarios = [dev_data_path+"/Hydrology/sce1", dev_data_path+"/Hydrology/sce2"]

    date_range = ["1900-01-01", None]

    # Read in index data
    # NOTE: Left most column will be used as the DataFrame index
    indexes = FileHandle.importFiles(dev_data_path+"/Ecology/index", ext=".csv", index_col=0, walk=False)
    indexes = indexes["index"] #Remove parent folder listing from Dict, as this is unneeded

    # read in asset table
    #This could be set as class attribute as it is used as a global in the R script
    asset_table = FileHandle.loadCSV(dev_data_path+"/Ecology/Water_suitability_param.csv")

    # read in weights
    weights = indexes["weights"]

    #change headers to lowercase to make it consistent with other csvs
    weights.columns = [x.lower() for x in weights.columns]

    # Set up additional parameters:
    # Set up weight for groundwater index
    gw_weight = 0.2

    # For DSS, can use RRGMS only as a minimum.
    specieslist = ["RRGMS", "RRGRR"]

    FlowIndexer = FlowSuitability(asset_table, specieslist, indexes, weights)

    #Generate default index column choice for each species, and each variable
    #Stores result as an attribute (default_index_cols)
    FlowIndexer.generateDefaultIndexCols()

    #Could specify this and pass to generateEnvIndex() as the species_col parameter
    #species_col should look like:
    # {
    #   'RRGMS': {
    #       'timing': 'MFAT1', 
    #       'duration': 'MFAT1', 
    #       'dry_period': 'MFAT1', 
    #       'gwlevel': 'Index', 
    #       'salinity': 'Index'
    # }, 'RRGRR': {
    #       'timing': 'MFAT1', 
    #       'duration': 'MFAT1', 
    #       'dry_period': 'Index', 
    #       'gwlevel': 'Index', 
    #       'salinity': 'Index'
    #   }
    # }

    species_cols = {
        'RRGMS': {
            'timing': 'MFATwoodland', 
            'duration': 'MFATwoodland', 
            'dry_period': 'Roberts', 
            'gwlevel': 'Index', 
            'salinity': 'Index'
     }, 'RRGRR': {
            'timing': 'Roberts', 
            'duration': 'Roberts', 
            'dry_period': 'Index', 
            'gwlevel': 'Index', 
            'salinity': 'Index'
        }
    }

    #This is unused at the moment
    # weighted = lambda d, gweight: d[1]*gweight + d[2]*(1-gweight)

    for scenario_dir in xrange(0, len(scenarios)):

        scen = scenarios[scenario_dir]

        scen_name = scen.split('/')[-1]

        scenario_data = FileHandle.importFiles(scen, index_col="Date", parse_dates=True, date_range=date_range, dayfirst=True) #read in all gauges within each scenarios

        #For each asset, generate flow indexes for each species
        for j in xrange(0, len(asset_table.index)):

            flow_indexes = FlowIndexer.generateEnvIndex(asset_id=j, scen_data=scenario_data, ecospecies=specieslist, species_cols=species_cols) #species_cols=FlowIndexer.default_index_cols, gswfun=weighted

            #For development purposes only. Display index results for each species
            print scen_name, "Asset {id}".format(id=j+1)
            for species in specieslist:

                save_folder = "./Integrated/Modules/Ecology/Outputs/{s}/asset_{asset}/{sp}".format(s=scen_name, asset=j+1, sp=species)

                species_index = flow_indexes[species]

                print species
                print "---- Groundwater ----"
                FileHandle.writeCSV(species_index['gw'], save_folder, "gw.csv")
                # print species_index['gw']
                print "---------------------"
                print "---- Surface Water ----"
                FileHandle.writeCSV(species_index['sw'], save_folder, "sw.csv")
                # print species_index['sw']
                print "---------------------"
                print "---- Water Index ----"
                FileHandle.writeCSV(species_index['water_index'], save_folder, "water_index.csv")
                # print species_index['water_index']
                print "---------------------"
            #End for

            #Save indexes to file or something?

        #End for

    #End for

