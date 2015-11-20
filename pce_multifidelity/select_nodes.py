from numpy import dot, array, arange, zeros, empty, argmax, finfo, sqrt
def select_nodes(V, N):
    # The columns of $V$ are the $M$ candidate outputs of the low-fidelity model
    # $V = u^L(\Gamma)=[ u^L(\mathbf{z}_1), u^L(\mathbf{z}_2) \cdots u^L(\mathbf{z}_M)  ]$.
    # $N$ is number of interpolation nodes/ high-fidelity runs
    M = V.shape[1]; assert N <= M;
    # Elements of $w$ are the norms for corresponding parameter $\mathbf{z}_m$ 
    w = array([dot(V[:, m], V[:, m]) for m in range(M)])
    # $P$ is the permutation vector
    P = arange(M, dtype=int) 
    # $L$ is the Cholesky factor
    L = zeros((M, N))
    r = empty((M))
    for n in range(N):
        # Choose largest norm for the next pivot/ interpolation point 
        p = argmax(w[n:M]) + n 
        # Avoid ill-conditioning if norm is less than machine precision
        if w[p] < 2*finfo( float ).eps:
            print 'Grammian is numerically singular...The grammian has rank %s and size %s'%(n,M)
            n -= 1 
            break
        # Update indices in $P$ and swap columns $n$ and $p$ of $V$, $L$, and $w$
        P[[n, p]] = P[[p, n]]
        V[:, [n, p]] = V[:, [p, n]]
        L[[n, p], :] = L[[p, n], :]
        w[[n, p]] = w[[p, n]]
        # Update $L$
        for t in range(n+1, M):
            r[t] = dot(V[:, t], V[:, n]) - sum([ L[t, j]*L[n, j] for j in range(n)]) 
        L[n, n] = sqrt(w[n])
        for t in range(n+1, M):
            L[t, n] = r[t]/L[n, n]
            w[t] = w[t] - L[t, n]**2
    # Truncate the Cholesky factor and permutation vector
    L = L[:n+1, :]
    P = P[:n+1] 
    return P, L
    # Note that $L L^T = V^T V$ where $V$ is the input $V$ with columns permuted according to $P$

