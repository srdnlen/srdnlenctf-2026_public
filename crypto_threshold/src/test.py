from sage.all import *
from ts import TSParam, TS
import random, tqdm

nsamples = 96

param = TSParam(N=16, T=8)
me = TS(param)
Rq = param.Rq

c = Rq.sample_in_ball(param.tau)
s = Rq.uniform()
rs = [Rq.gaussian(param.sigma_w) for _ in range(nsamples)]
me.i = 0
j = random.randrange(1, param.N)
ls = dict()
while len(ls) < nsamples:
    S = [me.i, j]
    while len(S) < param.T:
        x = random.randrange(param.N)
        if x not in S:
            S.append(x)
    S = tuple(sorted(S))
    if S in ls:
        continue
    ls[S] = me.lagrange_coeff(j, S)
ls = list(ls.values())
zs = [c * l * s + r for r, l in zip(rs, ls)]

d = 27
z0s, z1s = zip(*[z.power2round(d) for z in zs])

multiplicities = []
ids = []
coeffs = []
for i in tqdm.trange(param.n):
    # M = Matrix(ZZ, [ls, [-z1[i] * 2**d for z1 in z1s]])
    M = Matrix(ZZ, [ls, [-z[i] for z in zs]])
    L = Matrix.block(ZZ, [
        [1, M],
        [0, param.q],
    ])
    
    W = 2**31
    weights = [1, W] + [W >> 2 for _ in range(L.ncols() - 2)]
    Q = Matrix.diagonal(ZZ, weights)

    L *= Q
    L = L.LLL()
    L *= Q.inverse()

    # find the shortest vector and solution
    shortest_vector = None
    shortest_solution = None
    rows = iter(L.rows())
    while shortest_vector is None or shortest_solution is None:
        row = next(rows, None)
        if row is None:
            if shortest_vector is None:
                break  # there is no shortest vector which is non-zero mod q
            raise ValueError("no solution found")
        if row % param.q == 0:
            continue
        if shortest_solution is None and abs(row[1]) == 1:
            shortest_solution = row * sgn(row[1])
        elif shortest_vector is None and row[1] == 0:
            shortest_vector = row
    
    if shortest_solution[0] % param.q == (c * s)[i] % param.q:
        coeffs.append(shortest_solution[0] % param.q)
        multiplicities.append(L.ncols() - L.column(0).list().count(0))
        continue
    else:
        continue

    raise ValueError("shortest vector does not match")

    row1, row2 = L[1], L[2]
    assert abs(row2[1]) == W and row1[1] == 0
    guess1 = row2 * sgn(row2[1])
    guess2 = guess1 + row1
    guess3 = guess1 - row1

    if guess1[0] % param.q == (c * s)[i] % param.q:
        coeffs.append(guess1[0] % param.q)
    else:
        raise ValueError(f"no valid row found for coefficient {i}")

    multiplicities.append(L.ncols() - L.column(0).list().count(0))
    for j, row in enumerate(L):
        row *= sgn(row[1])
        if row[1] == W:
            # assert row[0] % param.q == (c * s)[i] % param.q
            coeffs.append(row[0] % param.q)
            break
    else:
        raise ValueError(f"no valid row found for coefficient {i}")
print(len(coeffs))
# guess = Rq(coeffs)