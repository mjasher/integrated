#main_hydro_dev.py

if __name__ == '__main__':

    import numpy as np
    import pandas as pd

    from integrated.Modules.Core.Handlers.FileHandler import FileHandler
    from Hydrology import Hydrology

    import datetime

    #Set up the file handler
    FileHandle = FileHandler()

    #Import all the files from the data directory
    data_path = "data"
    data = FileHandle.importFiles(data_path, ext=".csv", walk=False, dayfirst=True)
    data = data["data"] #Remove parent directory from listing

    #Set node_ids as index where possible
    for name, df in data.iteritems():
        try:
            df.index = df['node']
        except KeyError as e:
            #Doesn't have node column
            #Safe to skip
            continue
        #End try
    #End for

    #Create a Hydrology Object
    Hydro = Hydrology(data)

    #Define starting time and the end of scenario range
    # start_date = datetime.date(year=2005, month=9, day=1)
    # end_date = datetime.date(year=2006, month=8, day=31)

    start_date = datetime.date(year=1900, month=9, day=1)
    step = 1 #number of days for each timestep

    #No starting values, could pass a Pandas dataframe with initial results
    #expected Dataframe columns are node_id, calc_type (IHACRES, Routing, etc.), to_node, storage (initial water volume), prev_store
    # results = None

    import time

    s = time.time()

    results = None

    for ts in xrange(step, 365, step):

        last_timestep = start_date + datetime.timedelta(days=ts-step)
        last_timestep = str(last_timestep.strftime('%d/%m/%Y'))
        loop_timestep = start_date + datetime.timedelta(days=ts)
        loop_timestep = str(loop_timestep.strftime('%d/%m/%Y'))

        results = Hydro.run(loop_timestep, last_timestep, data=results)
        
    #End for


    print "Total script time: {st}".format(st=time.time() - s)

    print "Time spent prepping vars: {ts}".format(ts=Hydro.prep_time)
    print "Time spent climate vars: {ts}".format(ts=Hydro.climate_prep)
    print "Time taken doing calculations: {ts}".format(ts=Hydro.calc_time)
    print "    Summing node inflows: {ts}".format(ts=Hydro.inflow_time)
    print "    Time spent on Routing: {ts}".format(ts=Hydro.route)
    print "        Time spent on prepping routing vars: {ts}".format(ts=Hydro.route_i)
    print "        Calculating Routing: {s}".format(s=Hydro.Routing.runtime)
    print "    Time spent on IHACRES: {ts}".format(ts=Hydro.ih)
    print "        Time prepping data: {ts}".format(ts=Hydro.IHACRES.prep_time)
    print "            Climate: {ts}".format(ts=Hydro.IHACRES.get_climate)
    print "            Params : {ts}".format(ts=Hydro.IHACRES.get_params)
    print "        Calculating IHACRES: {ts}".format(ts=Hydro.IHACRES.calc_time)
    print "    Time spent on Dam: {ts}".format(ts=Hydro.dam)

    #Collate results
    deficit_df = pd.DataFrame()
    RRstorage_df = pd.DataFrame()
    flow_df = pd.DataFrame()
    storage_df = pd.DataFrame()
    level_df = pd.DataFrame()
    for timestep in results:

        temp_df = results[timestep]
        temp_df.index = temp_df['node_id']

        cols = temp_df['node_id']

        deficit_df = deficit_df.append(pd.DataFrame({timestep: temp_df['deficit']}, index=temp_df['node_id']).transpose())
        RRstorage_df = RRstorage_df.append(pd.DataFrame({timestep: temp_df['RRstorage']}, index=temp_df['node_id']).transpose())
        flow_df = flow_df.append(pd.DataFrame({timestep: temp_df['flow']}, index=temp_df['node_id']).transpose())
        storage_df = storage_df.append(pd.DataFrame({timestep: temp_df['storage']}, index=temp_df['node_id']).transpose())
        level_df = level_df.append(pd.DataFrame({timestep: temp_df['level']}, index=temp_df['node_id']).transpose())

    #End for

    #Resort dataframe into correct order (this stuffs up initially as it attempts to sort the datetime as strings)
    deficit_df.index = pd.to_datetime(deficit_df.index, dayfirst=True)
    deficit_df = deficit_df.sort_index()

    RRstorage_df.index = pd.to_datetime(RRstorage_df.index, dayfirst=True)
    RRstorage_df = RRstorage_df.sort_index()

    flow_df.index = pd.to_datetime(flow_df.index, dayfirst=True)
    flow_df = flow_df.sort_index()

    storage_df.index = pd.to_datetime(storage_df.index, dayfirst=True)
    storage_df = storage_df.sort_index()

    level_df.index = pd.to_datetime(level_df.index, dayfirst=True)
    level_df = level_df.sort_index()


    import matplotlib.pyplot as plt

    # Define 2x2 display
    fig, axes = plt.subplots(nrows=2, ncols=3)

    #Options to pass to plot function
    #See http://pandas.pydata.org/pandas-docs/stable/visualization.html#basic-plotting-plot
    options = dict(
        sharex=False,
        legend=False
    )

    #Calling plot() for a DataFrame automagically adds the figure/subplot to the "plt" plotting object
    #axes[] indicates row/column position (zero indexed of course)
    deficit_df.plot(ax=axes[0,0], title='Deficits', **options)
    RRstorage_df.plot(ax=axes[0,1], title='RRStorage', **options)
    flow_df.plot(ax=axes[1,0], title='Flow', **options)
    storage_df.plot(ax=axes[1,1], title='Storage', **options)
    level_df.plot(ax=axes[1,2], title='Level', **options)

    #Also move legend outside of plotting window
    plt.legend(loc='center left', bbox_to_anchor=(1.0, 1.0), title='Node ID') 
    plt.subplots_adjust(right=0.8) #Scale plots to fit legend

    #Generate the plot and display it
    plt.plot()
    plt.show()

    # # Example for saving results as a csv
    # save_path = "C:/temp/deficit_mod.csv"
    # deficit_df.to_csv(save_path)

    # save_path = "C:/temp/RRstorage_mod.csv"
    # RRstorage_df.to_csv(save_path)

    # save_path = "C:/temp/flow_mod.csv"
    # flow_df.to_csv(save_path)

    # save_path = "C:/temp/storage_mod.csv"
    # storage_df.to_csv(save_path)

