# Threshold

- **Category:** Crypto
- **Solves:** 8
- **Tag:** MLWE, Threshold Signature, LLL

## Description

I hope you'll like my FROST-like Threshold Signature on Lattices!

## Details

The challenge implements a threshold signature scheme similar to FROST but based on lattice assumptions (MLWE). The objective is to forge a valid signature on a specific target message using the threshold signature protocol provided.

## Solution

The file `ts.py` contains the implementation of the threshold signature scheme as the `TS` class. The class doc string links [this paper](https://eprint.iacr.org/2024/496.pdf) which describes the scheme in detail in Figure 8. By analyzing the scheme, one notices that the it is not properly implemented. 

Indeed, during the individual signing phase, each signer computes their partial signature as

$$\mathbf{z}_i = \mathbf{r}_i + c \cdot L_{S, i} \cdot \mathbf{s}_i$$

where $L_{S, i}$ is the Lagrange coefficient for signer $i$ in the set of signers $S$. Since the secret key shares $\mathbf{s}_i$ are uniform and $\mathbf{r}_i$ is sampled from a Gaussian distribution, then the high bits of $\mathbf{z}_i$ leak information about 

$$c \cdot L_{S, i} \cdot \mathbf{s}_i.$$

To exploit this leakage, one would need to gather some partial signatures from different signing sessions, i.e. different challenges $c$. Say we have $Q$ different $\mathbf{z}_i^{(j)}$ for $j=1, \ldots, Q$ corresponding to challenges $c^{(j)}$. We should then be able to set up $\ell$ lattice bases, one for each entry of $\mathcal{R}_q^\ell$, that encode the relation

$$\mathbf{z}_i^{(j)} - c^{(j)} \cdot L_{S, i} \cdot \mathbf{s}_i = \mathbf{r}_i^{(j)} \ll q$$

each with the respective entry of $\mathbf{s}_i$ as unknown. So the problem reduces to finding a short vector over these lattices. The issue is that these lattices have dimension $(Q + 1) n$ each, which is quite large for our parameters.

> The above approach is the only one I could think of to attack the scheme. Linear programming techniques do not seem to apply here, as the operations are mod $q$ and not over the integers. Also, representing the above in the NTT domain does not seem to help either.

The main cause of the above issue are the different challenges $c^{(j)}$ multiplying the secret share $\mathbf{s}_i$. These ensure that the unknowns are not aligned for different signing sessions, which would allow to reduce the lattice dimension.

One peculiarity of FROST-like schemes is that the signers can pre-compute and publish their commitments $\mathbf{w}_i$ before knowing the message to be signed. This means that the challenge $c$ is computed as $c = H(\mathsf{vk}, \mathsf{M}, \mathbf{w})$ with

$$\mathbf{w} = \left\lfloor \sum_{i \in S} \mathbf{w}_i \right\rceil_{\gamma_w}.$$

So, if each signer commitment cache is independent of the others, an attacker can try to manipulate the overall commitment $\mathbf{w}$ by choosing its own commitment $\mathbf{w}_i$ maliciously. In particular, if the attacker can set $\mathbf{w}$ to a value of its choice and ask for a joint signature on a fixed message $\mathsf{M}$ multiple times, the challenge $c$ will be the same for all signing sessions.

This is exactly the case in our implementation, where we have independent commitment caches for each signer. Thus, we can set the overall commitment $\mathbf{w}$ to a constant value for each signing session, ensuring that the challenge $c$ remains the same. 

We now relax our notation by 
- fixing implicitly a signer $i$ of which we want to recover the secret share $\mathbf{s}_i$, so that $\mathbf{s} = \mathbf{s}_i$, $\mathbf{r} = \mathbf{r}_i$ and so on, and
- assuming that $\ell = 1$ for simplicity, so that all vectors in $\mathcal{R}_q^\ell$ become simply polynomials in $\mathcal{R}_q$ denoted by lowercase letters.

Thus, the above relation simplifies to

$$z_i^{(j)} - L_{S^{(j)}} \cdot (c \cdot s)_i = r_i^{(j)} \ll q$$

for each signing session $j = 1, \ldots, Q$ and each coefficient $i = 1, \ldots, n$ of the polynomials in $\mathcal{R}_q$.

If we fix the unknown as $(c \cdot s)_i$, we can set up the following lattice basis

$$B = \begin{pmatrix}
1 & 0 & L_{S^{(1)}} & L_{S^{(2)}} & \cdots & L_{S^{(Q)}} \\
0 & 1 & -z_i^{(1)} & -z_i^{(2)} & \cdots & -z_i^{(Q)} \\
0 & 0 & q & 0 & \cdots & 0 \\
0 & 0 & 0 & q & \cdots & 0 \\
\vdots & \vdots & \vdots & \vdots & \ddots & \vdots \\
0 & 0 & 0 & 0 & \cdots & q
\end{pmatrix}$$

then the vector

$$\Big( (c \cdot s)_i, 1, -r_i^{(1)}, -r_i^{(2)}, \ldots, -r_i^{(Q)} \Big)$$

is given by

$$\Big( (c \cdot s)_i, 1, h_1, h_2, \ldots, h_Q \Big) \cdot B$$

with $h_j \in \mathbb{Z}$ such that 

$$r_i^{(j)} = z_i^{(j)} - (c \cdot s)_i \cdot L_{S^{(j)}} - h_j \cdot q.$$

Thus, with enough signing sessions $Q$ and good rescaling of the basis, we can expect to recover the unknown $(c \cdot s)_i$ by means of lattice basis reduction and shortest solution finding. More precisely
- information theoretically speaking, we need $Q > \log_2 q$ to recover the secret coefficient with high probability (in [solve.py](./src/solve.py) I set `nsamples = 64` since $q \approx 2^{31}$);
- since $r_i^{(j)}$ follows a centered discrete Gaussian distribution with standard deviation $\sigma_r$, we expect $\vert r_i^{(j)} \vert \approx \sigma_w \sqrt{2 / \pi}$ and thus we can rescale the basis accordingly, although with Gaussians this is not as effective as with uniform distributions.

Since we need to recover $T$ different secret shares $\mathbf{s}_i$ to reconstruct the secret key $\mathbf{s}$ via Lagrange interpolation, we can repeat the above procedure for $T$ different signers $i$. This requires us to perform $T \cdot \ell \cdot n = 8 \cdot 5 \cdot 256 = 10240$ lattice reductions.

> For some reason, I started developing [my solution](./src/solve.py) taking only the most significant bits of each coefficient of the partial signatures $\mathbf{z}_i^{(j)}$ to build the lattice bases. This makes the lattice reduction sligtly faster but often fails to recover the correct secret coefficients. To understand whether the recovered solution is correct, I check if the 2-norm of the masks $\mathbf{r}_i^{(j)}$ is below a certain bound.
