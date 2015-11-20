import chaospy as cp
import numpy
import time
import matplotlib.pylab as plt
import multiprocessing
import sys
sys.path.append("../groundwater/")
import campaspe_toy
from parallel_utils import parmap

# pool = multiprocessing.Pool(multiprocessing.cpu_count())

# The model solver
def u(z):
	return campaspe_toy.run(*z, nrow=10)

# Defining the random input distributions:
dists = [cp.Uniform(0,0.5) for i in range(3)]
dists.append(cp.Uniform(-200.,50.))
dist = cp.J(*dists)

num_tests = 100
order = 3

## Polynomial chaos expansion
## using Pseudo-spectral method and Gaussian Quadrature
P, norms = cp.orth_ttr(order-2, dist, retall=True)
nodes, weights = cp.generate_quadrature(order+1, dist, rule="G", sparse=False)
# solves = [u(s) for s in nodes.T]
solves = parmap(u, nodes.T) #[u(s) for s in nodes.T]
U_hat = cp.fit_quadrature(P, nodes, weights, solves, norms=norms)

test_inputs = dist.sample(num_tests)
test_outputs = numpy.array([u(s) for s in test_inputs.T])
surrogate_test_outputs = numpy.array([U_hat(*s) for s in test_inputs.T])

print "mean l2 error", numpy.mean(numpy.linalg.norm(test_outputs-surrogate_test_outputs, axis=0))
print "mean l2 norm", numpy.mean(numpy.linalg.norm(test_outputs, axis=0))

# scatter for all QOI
num_qoi = test_outputs.shape[1]
for qoi_i in range(num_qoi):
	plt.subplot(numpy.ceil(num_qoi/3.),3,qoi_i+1)
	plt.scatter(test_outputs[:, qoi_i], surrogate_test_outputs[:, qoi_i])
	plt.plot([test_outputs[0, qoi_i], test_outputs[-1, qoi_i]], [test_outputs[0, qoi_i], test_outputs[-1, qoi_i]], '--')
	plt.title("qoi %d" % qoi_i)
plt.show()

# a few random test samples
num_plot_samples = 9
randoms = numpy.random.choice(num_tests, size=num_plot_samples, replace=False)
for i, sample_i in enumerate(randoms):
	plt.subplot(numpy.ceil(num_plot_samples/3.), 3, i+1)
	plt.plot(test_outputs[sample_i, :], '.')
	plt.plot(surrogate_test_outputs[sample_i, :])
	plt.title("sample %d" % sample_i)
plt.show()
