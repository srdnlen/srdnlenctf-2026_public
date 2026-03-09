# Lightweight

- **Category:** Crypto
- **Solves:** 46
- **Tag:** Symmetric, Differential-linear

## Description

Welcome Ascon - Lightweight Cipher since 2014.

## Details

The server is an encryption oracle for 4 rounds of the Ascon AEAD scheme. The user cannot choose the nonce, but can choose the differential of the nonce and both $E(K, N)$ and $E(K, N \oplus \Delta)$ are returned. The goal is to recover the key.

## Solution

The file `server.c` implements the encryption oracle. Here is a brief description of Ascon:
- The key $K$ has 128 bits, represented as 2 64-bit words $K_0, K_1$.
- The nonce $N$ has 128 bits, represented as 2 64-bit words $N_0, N_1$.
- The state $S$ is a 320-bit vector, represented as 5 64-bit words, initialized as $S = (IV, K_0, K_1, N_0, N_1)$ where $IV$ is a fixed initialization vector.
- The internal permutation $p := p_L \circ p_S \circ p_C$ is a composition of three permutations:
  - $p_C$ is a constant addition layer that adds round constants to the state;
  - $p_S$ is a non-linear layer that applies an S-box to the state vertically, i.e. to each 5-bit column $S_0[i], S_1[i], S_2[i], S_3[i], S_4[i]$ for $i = 0, \ldots, 63$; and
  - $p_L$ is a linear layer that applies a linear transformation to the state orizontally, i.e. to each 64-bit word $S_j$ for $j = 0, \ldots, 4$.

For a more detailed description of the scheme, see [NIST SP 800-232](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-232.pdf).

On the server, the encryption oracle applies 4 rounds of the above permutation to the state, and then returns $E(K, N) = S_0 \parallel S_1$ as the ciphertext. The user can choose a differential $\Delta = \Delta_0 \parallel \Delta_1$ for the nonce, and obtain both $E(K, N)$ and $E(K, N \oplus \Delta)$.

In the literature, there are mainly two approaches to perform a key recovery attack on Ascon: 
- **Cube attack**: This approach exploits the algebraic structure of the cipher to recover the key by solving a system of equations. However, this is only possible if we have control over the nonce, which is not our case.
- **Differential-linear attack**: This approach exploits differential-linear distinguishers to infer information about the key. Since we have control over the differential of the nonce, this approach is more promising.

In the paper [Cryptanalysis of Ascon](https://eprint.iacr.org/2015/030.pdf), the authors present a 4-round differential-linear attack on Ascon with complexity $2^{18}$. The attack relies on the poor diffusion that 3.5 rounds of Ascon provide. The attack should work in theory, but in what follows, we will consider another approach.

In [Revisiting Differential-Linear Attacks...](https://eprint.iacr.org/2024/255.pdf) the authors introduce a new tool [DL](https://github.com/hadipourh/DL/tree/main) to find differential-linear distinguishers on many ciphers, including Ascon. We will use this tool to find our 4-round differential-linear distinguishers, and then use it to perform a key recovery attack.

The general idea of DL attacks is to divide the cipher into three parts: $E = E_\ell \circ E_m \circ E_u$, where
- $E_u$ is the upper part of the cipher, which consists of the first few rounds;
- $E_\ell$ is the lower part of the cipher, which consists of the last few rounds; and
- $E_m$ is the middle part of the cipher, which consists of the rounds in between $E_u$ and $E_\ell$.

We consider all possible differential trails for $E_m$ and all possible linear approximations for $E_m^{-1}$. By intersecting the two trails, we can find a differential-linear distinguisher for $E_m$. That is, a pair of input difference $\Delta_m$ and output mask $\lambda_m$ such that we have a non-negligible bias, i.e. 

$$\left| \Pr_{S} \left[ \lambda_m \cdot E_m(S) = \lambda_m \cdot E_m(S \oplus \Delta_m) \right] - \frac{1}{2} \right|$$

is non-negligible.

Then, for the upper part $E_u$, we can find a pair of input difference $\Delta_i$ that propagates to $\Delta_m$ with high probability. Similarly, for the lower part $E_\ell$, we can consider $E_\ell^{-1}$ and find input mask $\lambda_o$ that propagates to $\lambda_m$ with high probability. 

Thus, our DL distinguisher will be the pair of input difference $\Delta_i$ and output mask $\lambda_o$ such that we have a non-negligible bias, i.e.

$$\left| \Pr_{S} \left[ \lambda_o \cdot E(S) = \lambda_o \cdot E(S \oplus \Delta_i) \right] - \frac{1}{2} \right|$$

is non-negligible over all possible states $S$, that in our case are limited to $S = (IV, K_0, K_1, N_0, N_1)$ with the input difference $\Delta_i$ applied to the nonce words $N_0$ and $N_1$.

All the above steps are done by the tool [DL](https://github.com/hadipourh/DL/tree/main), by encoding the problem as a constraint satisfaction problem and solving it with a constraint solver, e.g. Google OR-Tools. Using the tool we can choose the number of rounds for $E_u$, $E_m$, and $E_\ell$, e.g. 1, 3 and 0 respectively, and find a 4-round differential-linear distinguisher for Ascon.

By itself the tool only gives us the distinguisher with the best bias, and so it could output a difference or mask that we cannot use, e.g. a difference applied to the key. However, we can add some artificial constraints to the problem by modifying the file [attack.mzn](https://github.com/hadipourh/DL/blob/main/ascon/attack.mzn).

We uncomment these constraints to ensure that the input difference is applied only to the nonce, and that the output mask is active only in $S_0$ and $S_1$, which are the two words that are returned as ciphertext.
```minizinc
% Ascon-AEAD
% ####################################################
% Difference can be in X[3] and X[4]
% Output mask should be zero in X[2], X[3], X[4]

constraint forall(row in 0..2, column in 0..63)(xu[0, row, column] = 0);
constraint forall(row in 2..4, column in 0..63)(xl[RL, row, column] = 0);
% ####################################################
```
Since Ascon is rotation-invariant within the 64-bit words, we add some constraints to ensure that the input difference is active only on the most significant bits of $N_0$ and $N_1$. Similarly, we can add some constraints to ensure a particular $\Delta_i$ or $\Delta_m$.
```minizinc
% Artificial constraints to obtain a 4-round DL distinguisher with a specific target input/output difference in the first sbox layer
constraint forall(row in 0..4, column in 1..63)(xu[0, row, column] = 0);  % LSBs all zero
% Delta_i difference
constraint xu[0, 0, 0] = 0;
constraint xu[0, 1, 0] = 0;
constraint xu[0, 2, 0] = 0;
constraint xu[0, 3, 0] = 1;
constraint xu[0, 4, 0] = 1;
constraint forall(row in 0..4, column in 1..63)(yu[0, row, column] = 0);  % LSBs all zero
% Delta_m difference
constraint yu[0, 0, 0] = 1;
constraint yu[0, 1, 0] = 0;
constraint yu[0, 2, 0] = 0;
constraint yu[0, 3, 0] = 0;
constraint yu[0, 4, 0] = 0;
```
As an example, [dlrepo.patch](./src/dlrepo.patch) contains a diff that adds the above constraints to [attack.mzn](https://github.com/hadipourh/DL/blob/main/ascon/attack.mzn).

We fix the input difference $\Delta_i[i] = (1, 1)$ for some $i$, then, by minimizing the hamming weight of $\Delta_m$, we set $\Delta_m[i] = (1, 0, 0, 0, 0)$ and $\Delta_m[i] = (0, 0, 0, 0, 1)$. These are the only differences with hamming weight 1 that we can achieve by controlling $N_0$ and $N_1$. We experimentally determine their bias with [test.py](./src/test.py) (in truth, these biases are multiplied by $2$ since a bias of $0.5$ means that the probability is $1$, and a bias of $-0.5$ means that the probability is $0$).

|   $\Delta_m[i]$   | Bias $K[i] = (0, 0)$ | Bias $K[i] = (0, 1)$ | Bias $K[i] = (1, 0)$ | Bias $K[i] = (1, 1)$ |
|-------------------|----------------------|----------------------|----------------------|----------------------|
| $(1, 0, 0, 0, 0)$ |        $0.5$         |      $\sim 0.0$      |      $\sim 0.0$      |      $\sim 0.0$      |
| $(0, 0, 0, 0, 1)$ |        $0.5$         |       $-0.25$        |       $-0.25$        |        $0.5$         |

Thus, we can divide the key bits $K[i]$ into three sets and the only combination of key bits that we cannot distinguish is $K[i] = (0, 1)$ and $K[i] = (1, 0)$. So we only need to find another distinguisher such that the bias is different for these two cases.

After finding such a distinguisher, it is only a matter of querying the server with the appropriate input differences, applying the mask to the output, and checking the bias to recover the key bits. The code for this part is implemented in [solve.py](./src/solve.py). Most of the time, we can recover 128 bits of the key with $2^{15}$ queries, which is less than the maximum allowed $2^{16}$ queries.
