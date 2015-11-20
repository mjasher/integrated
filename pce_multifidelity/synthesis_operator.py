from numpy import dot
from numpy.linalg import inv, cond
def synthesis_operator(LF_selected_values, HF_selected_values, L, LF_new):
	# LF_selected_values is $u^L(\gamma)$
	# HF_selected_values is $u^H(\gamma)$
	# L is the Cholesky product from the node selection algorithm
	# LF_new is $u^L(\mathbf{z})$
	G = dot(L,L.T)
	G_inv = inv( G )
	g = dot( LF_selected_values.T, LF_new )
	c = dot( G_inv, g )
	# MF_new approximates $u^H(\mathbf{z})$
	MF_new = dot( HF_selected_values, c ).squeeze()
	return MF_new, cond(G)