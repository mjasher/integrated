import flopy
import numpy as np
import os
import multiprocessing

#from Modules.Core.IntegratedModelComponent import Component

class Groundwater(object):

    def __init__(self, name, data_folder, flowpy_params, lrcd=None, **kwargs):

        """
        :param name: Model name
        :param data_folder: Folder to get data from
        """
        
        self.name = name
        self.data_folder = data_folder

        # Add RIV package to the MODFLOW model to represent rivers and channels
        #Create default lrcd (JUST FOR EXAMPLE)
        if lrcd is None:
            lrcd = {}
            lrcd[0] = [[0, 4, 0, 0.1, 100., -0.01],[0, 4, 1, 0.1, 100., -0.01],[0, 4, 2, 0.1, 100., -0.01],[0, 4, 3, 0.1, 100., -0.01],
                       [0, 4, 4, 0.1, 100., -0.01],[0, 4, 5, 0.1, 100., -0.01],[0, 4, 6, 0.1, 100., -0.01],[0, 4, 7, 0.1, 100., -0.01],
                       [0, 4, 8, 0.1, 100., -0.01],[0, 4, 9, 0.1, 100., -0.01]]  # layer, row, column, river stage, conductance, river bed

            self.lrcd = lrcd
        #End if

        #Assign flowpy params as class attribute
        self.flowpy_params = flowpy_params

        #Set all other kwargs as class attributes
        for key, value in kwargs.items():
            setattr(self, key, value)
        #End For

        self.flowpy_params['model_dir'] = os.path.join("../too_big_to_git", "MF_IO", name)

        #Generate flowpy parameters that are dependent on the given parameters
        self.generateParams()

    #End init()

    def generateParams(self):

        """
        Generate parameters based on other Flowpy parameters

        This doesn't return anything, just sets the parameters
        """

        domain_grid = self.flowpy_params['domain_grid']

        #Set other params, remember Python is pass-by-reference
        domain_grid['delr'] = domain_grid['Lx'] / domain_grid['ncol']
        domain_grid['delc'] = domain_grid['Ly'] / domain_grid['nrow']
        domain_grid['delv'] = (domain_grid['ztop'] - domain_grid['zbot']) / domain_grid['nlay']
        domain_grid['botm'] = np.linspace(domain_grid['ztop'], domain_grid['zbot'], domain_grid['nlay'] + 1)

    #End generateParams()

    def createDiscretisation(self):

        params = self.flowpy_params['domain_grid']
        timestep_params = self.flowpy_params['timestep_params']

        # Create discretisation object
        self.dis = flopy.modflow.ModflowDis(self.mf, params['nlay'], params['nrow'], params['ncol'], delr=params['delr'], delc=params['delc'], top=params['ztop'], botm=params['botm'][1:],
                               nper=timestep_params['nper'], perlen=timestep_params['perlen'], nstp=timestep_params['nstp'], steady=timestep_params['steady'])

    #End createDiscretisation()

    def setupBASPackage(self, nlay, nrow, ncol):

        # Variables for the BAS package
        ibound = np.ones((nlay, nrow, ncol), dtype=np.int32)
        strt = 10. * np.ones((nlay, nrow, ncol), dtype=np.float32)

        self.bas = flopy.modflow.ModflowBas(self.mf, ibound=ibound, strt=strt)

    #End setupBASPackage()

    def runMODFLOW(self):

        self.name += str(multiprocessing.current_process().name) # so each process has own files
        self.mf = flopy.modflow.Modflow(self.name, exe_name=self.flowpy_params['exe_name'], model_ws=self.flowpy_params['model_dir'])

        self.createDiscretisation()
        self.setupBASPackage(domain_grid['nlay'], domain_grid['nrow'], domain_grid['ncol'])

        # Add UPW package to the MODFLOW model to represent aquifers
        self.upw = flopy.modflow.ModflowUpw(self.mf, hk=domain_grid['hk'], vka=domain_grid['vka'], sy=domain_grid['sy'], ss=domain_grid['ss'], hdry=-999.9, laytyp=domain_grid['laytyp'])

        # Add RCH package to the MODFLOW model to represent recharge
        rchrate = 1.0E-3 * np.random.rand(domain_grid['nrow'], domain_grid['ncol'])
        self.rch = flopy.modflow.ModflowRch(self.mf, rech=rchrate, nrchop=1)

        # Add EVT package to the MODFLOW model to represent evapotranspiration
        evtr = 1.0E-4 * np.ones((domain_grid['nrow'], domain_grid['ncol']), dtype=np.float32)
        self.evt = flopy.modflow.ModflowEvt(self.mf, nevtop=3, evtr=evtr)

        riv = flopy.modflow.ModflowRiv(self.mf, stress_period_data=self.lrcd)

        # Add WEL package to the MODFLOW model to represent pumping wells
        lrcq = {}
        lrcq[0] = [[0, 7, 7, -100.]] # layer, row, column, flux
        self.wel = flopy.modflow.ModflowWel(self.mf, stress_period_data=lrcq)

        # Specify NWT settings
        self.nwt = flopy.modflow.ModflowNwt(self.mf, headtol=1.0E-3)
        #pcg = flopy.modflow.ModflowPcg(mf)  # if using mf 2005

        # Add OC package to the MODFLOW model
        self.oc = flopy.modflow.ModflowOc(self.mf)

        # Write the MODFLOW model input files
        self.mf.write_input()

        # Run the MODFLOW model
        success, buff = self.mf.run_model()
        if not success:
            raise Exception('MODFLOW did not terminate normally.')
        #End if

    #End runMODFLOW()

    def showResults(self):
        # Imports
        import matplotlib.pyplot as plt
        import flopy.utils.binaryfile as bf

        model_dir = flowpy_params['model_dir']

        domain_grid = self.flowpy_params['domain_grid']

        delr = domain_grid['delr']
        Lx = domain_grid['Lx']
        Ly = domain_grid['Ly']
        delc = domain_grid['delc']

        # Create the headfile object
        headobj = bf.HeadFile(os.path.join(model_dir, self.name+'.hds'))
        times = headobj.get_times()

        # Setup contour parameters
        levels = np.arange(1, 10, 1)
        extent = (delr/2., Lx - delr/2., delc/2., Ly - delc/2.)
        print 'Levels: ', levels
        print 'Extent: ', extent

        # Well point
        wpt = (750., 250.)

        # Make the plots
        mytimes = [1.0]
        for iplot, time in enumerate(mytimes):
            print '*****Processing time: ', time
            head = headobj.get_data(totim=time)
            #Print statistics
            print 'Head statistics'
            print '  min: ', head.min()
            print '  max: ', head.max()
            print '  std: ', head.std()

            #Create the plot
            plt.subplot(1, 1, 1, aspect='equal')
            plt.title('stress period ' + str(iplot + 1))
            plt.imshow(head[0, :, :], extent=extent, cmap='Spectral', vmin=head.min(), vmax=head.max())
            plt.colorbar()
            mfc = 'None'
            if (iplot+1) == len(mytimes):
                mfc='black'
            plt.plot(wpt[0], wpt[1], lw=0, marker='o', markersize=8,
                     markeredgewidth=0.5,
                     markeredgecolor='black', markerfacecolor=mfc, zorder=9)
            plt.text(wpt[0]+25, wpt[1]-25, 'well', size=12, zorder=12)
            model_map = flopy.plot.ModelMap(model=self.mf, dis=self.dis)
            linecollection = model_map.plot_grid()
            plt.show()
        #End for

    #End showResults()

#End Groundwater()

#Ordinarily, the script and the Class definition would be in separate files
if __name__ == '__main__':

    # Model domain and grid definition
    domain_grid = {
        'Lx': 1000.,
        'Ly': 1000.,
        'ztop': 0.,
        'zbot': -50.,
        'nlay': 1,
        'nrow': 10,
        'ncol': 10,
        'hk': 1.,
        'vka': 1.,
        'sy': 0.1,
        'ss': 1.e-4,
        'laytyp': 1
    }

    # Time step parameters
    timestep_params = dict(
        nper = 1,
        perlen = [1],
        nstp = [1],
        steady = [False]
    )

    name = 'Campaspe_toy'

    flowpy_params = {}
    flowpy_params['domain_grid'] = domain_grid
    flowpy_params['exe_name'] = 'modflow-nwt_64'
    flowpy_params['model_dir'] = os.path.join("../too_big_to_git", "MF_IO", name)
    flowpy_params['timestep_params'] = timestep_params

    # Add RIV package to the MODFLOW model to represent rivers and channels
    # lrcd = {}
    # lrcd[0] = [[0, 4, 0, 0.1, 100., -0.01],[0, 4, 1, 0.1, 100., -0.01],[0, 4, 2, 0.1, 100., -0.01],[0, 4, 3, 0.1, 100., -0.01],
    #            [0, 4, 4, 0.1, 100., -0.01],[0, 4, 5, 0.1, 100., -0.01],[0, 4, 6, 0.1, 100., -0.01],[0, 4, 7, 0.1, 100., -0.01],
    #            [0, 4, 8, 0.1, 100., -0.01],[0, 4, 9, 0.1, 100., -0.01]]  # layer, row, column, river stage, conductance, river bed

    # CampaspeToy = Groundwater(name, '', flowpy_params, lrcd=lrcd)

    #Demonstrating First Class Objects
    groundwater_systems = [Groundwater('A', '', flowpy_params), Groundwater('B', '', flowpy_params), Groundwater('C', '', flowpy_params)]

    #Layer records (?) for each river system
    lrcds = []
    lrcds = {   0:[[0, 4, 0, 0.1, 100., -0.01],[0, 4, 1, 0.1, 100., -0.01],[0, 4, 2, 0.1, 100., -0.01],[0, 4, 3, 0.1, 100., -0.01],
                   [0, 4, 4, 0.1, 100., -0.01],[0, 4, 5, 0.1, 100., -0.01],[0, 4, 6, 0.1, 100., -0.01],[0, 4, 7, 0.1, 100., -0.01],
                   [0, 4, 8, 0.1, 100., -0.01],[0, 4, 9, 0.1, 100., -0.01]],  # layer, row, column, river stage, conductance, river bed
                1:[[0, 4, 0, 0.1, 85., -0.01],[0, 4, 1, 0.1, 12., -0.01],[0, 4, 2, 0.1, 100., -0.01],[0, 4, 3, 0.1, 100., -0.01],
                   [0, 4, 4, 0.1, 45., -0.01],[0, 4, 5, 0.1, 67., -0.01],[0, 4, 6, 0.1, 100., -0.01],[0, 4, 7, 0.1, 100., -0.01],
                   [0, 4, 8, 0.1, 55., -0.01],[0, 4, 9, 0.1, 89., -0.01]],  # layer, row, column, river stage, conductance, river bed
                2:[[0, 4, 0, 0.1, 65., -0.01],[0, 4, 1, 0.1, 55., -0.01],[0, 4, 2, 0.1, 100., -0.01],[0, 4, 3, 0.1, 100., -0.01],
                   [0, 4, 4, 0.1, 45., -0.01],[0, 4, 5, 0.1, 11., -0.01],[0, 4, 6, 0.1, 100., -0.01],[0, 4, 7, 0.1, 100., -0.01],
                   [0, 4, 8, 0.1, 35., -0.01],[0, 4, 9, 0.1, 99., -0.01]]  # layer, row, column, river stage, conductance, river bed
                }

    #Running model for each river system
    num = 0
    for i in groundwater_systems:

        i.lrcd = lrcds[num]

        i.runMODFLOW()
        i.showResults()

        num = num + 1

    #End for

#End main


