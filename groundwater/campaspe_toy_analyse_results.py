import matplotlib.pyplot as plt
import flopy.utils.binaryfile as bf
import numpy as np

modelname = 'campaspe_toy'
# Grid details
Lx = 1000
Ly = 1000
ztop = 0
zbot = -20
nlay = 3
nrow = 10
ncol = 10
delr = Lx/ncol
delc = Ly/nrow
delv = (ztop-zbot)/nlay
botm = np.linspace(ztop, zbot, nlay + 1)

plt.subplot(1,1,1,aspect='equal')
hds = bf.HeadFile(modelname+'.hds')
head = hds.get_data(totim=1.0)
levels = np.arange(1,10,1)
extent = (delr/2., Lx - delr/2., Ly - delc/2., delc/2.)
plt.contour(head[0, :, :], levels=levels, extent=extent)
plt.show()