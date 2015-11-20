"""
Boilerplate for running the multi-fidelity stochastic collocation algorithm using a simple diffusion example
-----------------------------------------------------------------
authors: John Jakeman (jdjakem@sandia.gov) and Michael Asher (michael.james.asher@gmail.com)
date: August 2015
"""

import numpy
import matplotlib.pylab as plt

"""
Import 
    * HF_model and LF_model: high-fidelity and low-fidelity models
    * sample_inputs: function to produce samples from input distributions (for building and testing)
    * select_nodes: function to select collocation nodes
    * synthesis_operator: function to compute surrogate
-----------------------------------------------------------------
"""

from ellip import HF_model, LF_model, sample_inputs
from select_nodes import select_nodes
from synthesis_operator import synthesis_operator

"""
Settings 
-----------------------------------------------------------------
"""
# number of initial candidates/snapshots for low-fidelity model
num_lf_candidates = 100
# number of low-fidelity, multi-fidelity, and high-fidelity runs to do for testing
num_test_samples = 100
# number of interpolations nodes/high-fidelity runs
num_hf_runs = 3

"""
1. Evaluate the low-fidelity model $u^L$ on a candidate set $\Gamma$.
-----------------------------------------------------------------
"""
candidate_inputs = sample_inputs(num_lf_candidates)
lf_candidate_values = LF_model( candidate_inputs )

"""
2. Choose an ordered subset of $N$ nodes $\gamma$ using Algorithm 1.
-----------------------------------------------------------------
"""
pivots, L  = select_nodes(V=lf_candidate_values.copy(), N=num_hf_runs)
selected_inputs = candidate_inputs[:,pivots]
lf_selected_values = lf_candidate_values[:,pivots]

"""
3. Evaluate the high-fidelity $u_H$ model on $\gamma$.
-----------------------------------------------------------------
"""
hf_selected_values = HF_model( selected_inputs )

"""
4. Use $u_H(\gamma)$ to construct the interpolation operator 
    and evaluate at any $z$ using Algorithm 2 with input data $v = u^L(z)$.
-----------------------------------------------------------------
"""
test_inputs = sample_inputs(num_test_samples)
lf_test_values = LF_model( test_inputs )
mf_test_values, condition_number = synthesis_operator(lf_selected_values, hf_selected_values, L, lf_test_values)
hf_test_values = HF_model( test_inputs )

print('condition number= %.2e, 1/machine eps= %.2e' % (condition_number, 1./numpy.finfo(float).eps))
print("||HF-LF|| = %.2e" % (numpy.mean(numpy.linalg.norm(hf_test_values-lf_test_values, axis=0)) / numpy.sqrt(hf_test_values.shape[0])) )
print("||HF-MF|| = %.2e" % (numpy.mean(numpy.linalg.norm(hf_test_values-mf_test_values, axis=0)) / numpy.sqrt(hf_test_values.shape[0])))

# plot a few random LF, HF, and MF samples
rand_i = numpy.random.randint(num_test_samples, size=(6))
for i in range(len(rand_i)):
  plt.subplot(numpy.ceil(len(rand_i)/3.), 3, i+1)
  plt.plot(lf_test_values[:, rand_i[i]], '--', label="lf")
  plt.plot(hf_test_values[:, rand_i[i]], '-', label="hf")
  plt.plot(mf_test_values[:, rand_i[i]], 'o', label="mf")
  plt.title('sample '+str(rand_i[i]))
plt.legend()
plt.show()

# plot all LF candidates
for l in range(num_lf_candidates):
    plt.plot(lf_candidate_values[:,l], color='grey', alpha=0.3)

# plot chosen LF and HF
cm = plt.get_cmap('gist_rainbow') 
for l in range(num_hf_runs):
    plt.plot(lf_selected_values[:,l], 'x', color=cm(1.*l/num_hf_runs))
    plt.plot(hf_selected_values[:,l], color=cm(1.*l/num_hf_runs))
plt.title("Selected nodes")
plt.show()
