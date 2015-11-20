"""
Multi-fidelity solver for a 1D elliptic PDE with random coefficients and random forcing
-----------------------------------------------------------------
Originally from Mike Giles' MCMC code.
authors: John Jakeman (jdjakem@sandia.gov) and Michael Asher (michael.james.asher@gmail.com)
date: August 2015

2nd order central difference discretization of (c u')'(x)= - 50 Z^2, u(0)=0, u(1)=0
where Z = N(0,1)                    (Normal with unit variance)
and c(x) = 1 + a*x with a = U(0,1)  (uniformly distributed on (0,1))

"""

import numpy
import scipy.sparse
import scipy.stats

class ellip():
  # set up equation matrices
  def __init__(self, nf, num_QOI):
    hf  = 1./nf
    cf  = numpy.ones((nf))
    A0f = hf**(-2)*scipy.sparse.spdiags([cf[1:], -cf[1:]-cf[0:-1], cf[0:-1]],[-1.,0.,1.],nf-1,nf-1)
    cf  = (numpy.arange(1.,nf+1.)-0.5)*hf
    A1f = hf**(-2)*scipy.sparse.spdiags([cf[1:], -cf[1:]-cf[0:-1], cf[0:-1]],[-1.,0.,1.],nf-1,nf-1)
    
    self.cf  = numpy.ones((nf-1))

    self.A0f = A0f
    self.A1f = A1f
    self.num_QOI = num_QOI

  # interpolate with grid of num_QOI cells
  def post_process(self, uf):
      nf = len(uf)+1
      hf = 1./nf
      n_HF = self.num_QOI + 1
      h_HF = 1./n_HF
      # note boundary conditions (0.) are left off ends, add them here
      return numpy.interp(x=[h_HF*(i+1) for i in range(n_HF-1)], xp=[hf*(i+1) for i in range(-1, nf)], fp=numpy.concatenate(([0.0], uf, [0.0])))

  # solve equation for given random variables
  def run(self, x):
    U, Z = x

    uf = scipy.sparse.linalg.spsolve(-(self.A0f+U*self.A1f), (50.*Z**2*self.cf))
    return self.post_process(uf)

  # solve equation for each column
  def bulk_run(self, input_samples):
    num_samples = input_samples.shape[1]
    output_values = numpy.empty( (self.num_QOI, num_samples), float )
    for i in range( num_samples ):
      output_values[:,i] = self.run( input_samples[:,i] ).squeeze()
    return output_values

# set up two fidelities
n_HF  = 2**(9)
h_HF  = 1./n_HF

n_LF = 2**(2)
h_LF  = 1./n_LF

num_QOI = n_HF - 1

num_dims = 2

HF_model = ellip(nf=n_HF, num_QOI=num_QOI).bulk_run
LF_model = ellip(nf=n_LF, num_QOI=num_QOI).bulk_run

# should return (num_dims, num_samples)
def sample_inputs(num_samples):
    input_samples = numpy.random.RandomState().uniform(0.,1.,(num_dims, num_samples))
    input_samples[1,:] = scipy.stats.distributions.norm(loc=0., scale=1.).ppf(input_samples[1,:])
    return input_samples

if __name__ == '__main__':

  num_samples = 6
  zs = sample_inputs(num_samples)

  HFs = HF_model(zs)
  LFs = LF_model(zs)

  import matplotlib.pylab as plt
  for i in range(num_samples):
    plt.subplot(numpy.ceil(num_samples/3.), 3, i+1)
    plt.plot(HFs[:,i], label="HF")
    plt.plot(LFs[:,i], '--', label="LF")
  plt.suptitle("Low and high fidelity elliptic equation solutions for a few random inputs.")
  plt.legend()
  plt.show()