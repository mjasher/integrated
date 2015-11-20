import chaospy as cp
import numpy
import time
import matplotlib.pylab as plt

# The model solver
def u(x, a, I):
    return I*numpy.exp(-a*x)
x = numpy.linspace(0, 10, 1000)

# Defining the random input distributions:
a = cp.Uniform(0, 0.1)
I = cp.Uniform(8, 10)
dist = cp.J(a, I)

num_tests = 100
order = 4


## Polynomial chaos expansion
## using Pseudo-spectral method and Gaussian Quadrature
P, norms = cp.orth_ttr(order-2, dist, retall=True)
nodes, weights = cp.generate_quadrature(order+1, dist, rule="G", sparse=False)
solves = [u(x, s[0], s[1]) for s in nodes.T]
U_hat = cp.fit_quadrature(P, nodes, weights, solves, norms=norms)

test_inputs = dist.sample(num_tests)
test_outputs = numpy.array([u(x, s[0], s[1]) for s in test_inputs.T])
surrogate_test_outputs = numpy.array([U_hat(s[0], s[1]) for s in test_inputs.T])

print "mean l2 error", numpy.mean(numpy.linalg.norm(test_outputs-surrogate_test_outputs, axis=0))
print "mean l2 norm", numpy.mean(numpy.linalg.norm(test_outputs, axis=0))

i = 10
plt.scatter(test_outputs[:, i], surrogate_test_outputs[:, i])
plt.show()

plt.plot(test_outputs[:, i], '--')
plt.plot(surrogate_test_outputs[:, i], '.')
plt.show()



## Monte Carlo integration
# samples = dist.sample(10**4)
# u_mc = [u(x,*s) for s in samples.T]

# print "SHAPE", numpy.array(u_mc).shape

# # mc_mean = numpy.mean(u_mc, 0)
# # mc_var = numpy.var(u_mc, 0)

# print '%30s%10s%10s%10s%10s' % (" ", 'mean err', 'var err', 'time', 'samples')
# print '%30s%10f%10f%10f%10s' % ("MC", 0, 0, time.time()-t0, samples.shape)
# t0 = time.time()