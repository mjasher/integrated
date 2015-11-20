import flopy
import numpy as np
import os
import multiprocessing

def run(riv_stage_0, riv_stage_1, riv_stage_2, wel_0, nrow):
    modelname = 'campaspe_toy_'  
    modelname += str(multiprocessing.current_process().name) # so each process has own files

    exe_name = 'modflow-nwt_64'
    exe_name = '/home/mikey/Dropbox/raijin/MODFLOW-NWT_1.0.9/pymade_modflow_nwt'
    model_dir = os.path.join("../too_big_to_git", "MF_IO", modelname)
    mf = flopy.modflow.Modflow(modelname, exe_name=exe_name, model_ws=model_dir)

    #mf = flopy.modflow.Modflow(modelname, version='mf2005',exe_name='mf2005')

    # Grid details, these are quite 
    Lx = 1000
    Ly = 1000
    ztop = 0
    zbot = -20
    nlay = 3 #3
    # nrow = 10
    # ncol = 10
    ncol = nrow
    delr = Lx/ncol
    delc = Ly/nrow
    delv = (ztop-zbot)/nlay
    botm = np.linspace(ztop, zbot, nlay + 1)
    hk = 1.
    vka = 1.
    sy = 0.1
    ss = 1.e-4
    laytyp = 1

    # Time step parameters
    nper = 1
    perlen = [1]
    nstp = [1]
    steady = [False]

    # Create discretisation object
    dis = flopy.modflow.ModflowDis(mf, nlay, nrow, ncol, delr=delr, delc=delc, top=ztop, botm=botm[1:],
                                   nper=nper, perlen=perlen, nstp=nstp, steady=steady)

    # Variables for the BAS package
    ibound = np.ones((nlay, nrow, ncol), dtype=np.int32)
    strt = 10. * np.ones((nlay, nrow, ncol), dtype=np.float32)

    bas = flopy.modflow.ModflowBas(mf, ibound=ibound, strt=strt)

    # Add UPW package to the MODFLOW model to represent aquifers
    upw = flopy.modflow.ModflowUpw(mf, hk=hk, vka=vka, sy=sy, ss=ss, hdry=-999.9, laytyp=laytyp)

    # Add RCH package to the MODFLOW model to represent recharge
    rchrate = 1.0E-3 * np.ones((nrow, ncol))
    rch = flopy.modflow.ModflowRch(mf, rech=rchrate, nrchop=1)

    # Add EVT package to the MODFLOW model to represent evapotranspiration
    evtr = 1.0E-4 * np.ones((nrow, ncol), dtype=np.float32)
    evt = flopy.modflow.ModflowEvt(mf, nevtop=3, evtr=evtr)

    # Add RIV package to the MODFLOW model to represent rivers and channels
    lrcd = {0:[]}
    for i_col in range(ncol):
        if i_col < ncol/3:
            riv_stage = riv_stage_0
        elif i_col < 2*ncol/3:
            riv_stage = riv_stage_1
        else:
            riv_stage = riv_stage_2
        lrcd[0].append([0, nrow/2, i_col, riv_stage, 100., -0.01])

    # lrcd[0] = [[0, nrow/2, 0, riv_stage_0, 100., -0.01],[0, nrow/2, 1, riv_stage_0, 100., -0.01],[0, nrow/2, 2, riv_stage_1, 100., -0.01],[0, nrow/2, 3, riv_stage_1, 100., -0.01],
               # [0, nrow/2, 4, riv_stage_1, 100., -0.01],[0, nrow/2, 5, riv_stage_1, 100., -0.01],[0, nrow/2, 6, riv_stage_2, 100., -0.01],[0, nrow/2, 7, riv_stage_2, 100., -0.01],
               # [0, nrow/2, 8, riv_stage_2, 100., -0.01],[0, nrow/2, 9, riv_stage_2, 100., -0.01]]  # layer, row, column, river stage, conductance, river bed
    riv = flopy.modflow.ModflowRiv(mf, stress_period_data=lrcd)

    # Add WEL package to the MODFLOW model to represent pumping wells
    lrcq = {}
    lrcq[0] = [[0, nrow/3, nrow/3, wel_0]] # layer, row, column, flux
    wel = flopy.modflow.ModflowWel(mf, stress_period_data=lrcq)

    # Specify NWT settings
    nwt = flopy.modflow.ModflowNwt(mf, headtol=1.0E-3)
    #pcg = flopy.modflow.ModflowPcg(mf)  # if using mf 2005

    # Add OC package to the MODFLOW model
    oc = flopy.modflow.ModflowOc(mf)

    # Write the MODFLOW model input files
    mf.write_input()

    # Run the MODFLOW model
    success, buff = mf.run_model(silent=True)
    if not success:
        raise Exception('MODFLOW did not terminate normally.')

    # Imports
    import flopy.utils.binaryfile as bf

    # Create the headfile object
    headobj = bf.HeadFile(os.path.join(model_dir, modelname+'.hds'))
    times = headobj.get_times()

    heads = headobj.get_data(totim=1.0)


    return heads[0, nrow/3, :]


    # # Setup contour parameters
    # levels = np.arange(1, 10, 1)
    # extent = (delr/2., Lx - delr/2., delc/2., Ly - delc/2.)
    # print 'Levels: ', levels
    # print 'Extent: ', extent

    # # Well point
    # wpt = (750., 250.)

    # # Make the plots
    # mytimes = [1.0]
    # for iplot, time in enumerate(mytimes):
    #     print '*****Processing time: ', time
    #     head = headobj.get_data(totim=time)
    #     #Print statistics
    #     print 'Head statistics'
    #     print '  min: ', head.min()
    #     print '  max: ', head.max()
    #     print '  std: ', head.std()

    #     #Create the plot
    #     plt.subplot(1, 1, 1, aspect='equal')
    #     plt.title('stress period ' + str(iplot + 1))
    #     plt.imshow(head[0, :, :], extent=extent, cmap='Spectral', vmin=head.min(), vmax=head.max())
    #     plt.colorbar()
    #     mfc = 'None'
    #     if (iplot+1) == len(mytimes):
    #         mfc='black'
    #     plt.plot(wpt[0], wpt[1], lw=0, marker='o', markersize=8,
    #              markeredgewidth=0.5,
    #              markeredgecolor='black', markerfacecolor=mfc, zorder=9)
    #     plt.text(wpt[0]+25, wpt[1]-25, 'well', size=12, zorder=12)
    #     model_map = flopy.plot.ModelMap(model=mf, dis=dis)
    #     linecollection = model_map.plot_grid()
    #     plt.show()


if __name__ == '__main__':
    z = [0.1, 0.2, 0.1, -100.]
    import matplotlib.pyplot as plt
    lf_heads = run(*z, nrow=10)
    hf_heads = run(*z, nrow=100)
    plt.plot(np.linspace(0,1000,10), lf_heads, label='lf')
    plt.plot(np.linspace(0,1000,100), hf_heads, label='hf')
    plt.legend()
    plt.show()