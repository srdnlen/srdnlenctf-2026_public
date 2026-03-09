# FHAES

- **Category:** Crypto
- **Solves:** 58
- **Tag:** Garbled Circuits

## Description

Here it is! Fully Homomorphic AES encryption finally made practical.

## Details

The server implements a garbled circuit service that allows clients to evaluate AES encryption/decryption circuits on data chosen by the client. Moreover, the server supports some homomorphic operations between ciphertexts, allowing the client to build more complex circuits. The objective is to recover the server's AES key by using this garbled circuit service.

## Solution

The library `srdnlengarble` functions similarly to the Rust library [fancy-garbling](https://github.com/GaloisInc/swanky/tree/dev/edge/fancy-garbling), implementing garbled circuits directly in Python for ease of use. Also, it allows just-in-time circuit construction to build custom circuits.

The garbling scheme used is [Half Gates](https://eprint.iacr.org/2014/756.pdf)+[Free XOR](https://encrypto.de/papers/KSS09.pdf) which is one of the most efficient garbling schemes known at the time of writing.

As of [this paper](https://eprint.iacr.org/2023/530.pdf), at least for the considered implementations, Half Gates+Free XOR is secure against their attack. Turns out that for [fancy-garbling](https://github.com/GaloisInc/swanky/tree/dev/edge/fancy-garbling) and thus for `srdnlengarble`, the attack does apply.

The idea of the attack is to consider the case in which two input wires of an AND gate have the same index, i.e. their wire labels `A` and `B` are equal. Assuming `A == B`, the following truth table summarizes the possible garbled AND gate using the same notation as in the method `Garbler.__garble_and_gate`.

| `A & 1/B & 1` | `r` | `idx` | `a/b` | `hashA/hashB`      | `hashX/hashY`      | `gate0`             | `gate1`             |
|---------------|-----|-------|-------|--------------------|--------------------|---------------------|---------------------|
|   $0$         | $0$ |  $0$  |  $0$  | :x:                | :heavy_check_mark: | `hashA ^ hashX`     | `hashB ^ hashY ^ A` |
|   $0$         | $0$ |  $0$  |  $1$  | :heavy_check_mark: | :x:                | `hashA ^ hashX`     | `hashB ^ hashY ^ A` |
|   $1$         | $1$ |  $0$  |  $0$  | :x:                | :heavy_check_mark: | `hashA ^ hashX ^ D` | `hashB ^ hashY ^ A` |
|   $1$         | $1$ |  $0$  |  $1$  | :heavy_check_mark: | :x:                | `hashA ^ hashX ^ D` | `hashB ^ hashY ^ A` |

Where `D` is the global difference for Free XOR and `a/b` is the hidden bit of wire `A/B`. :heavy_check_mark: indicates the known values and :x: the unknown values for each case. We mainly have two cases to consider:
- if `a/b == 0`, then we know the value of `A/B` and thus, if we are in the case `A & 1/B & 1 == 1`, we can recover `D` from `gate0 ^ gate1`;
- if `a/b == 1`, then we know the value of `A ^ D/B ^ D` and thus, if we are in the case `A & 1/B & 1 == 0`, we can recover `D` from `gate0 ^ gate1`.

Thus, $50\%$ of the time, when the two input wires of an AND gate have the same index, the evaluator can recover the global difference `D`. Once `D` is known, recovering the server's AES key is a matter of solving a system of linear equations over $\mathbb{F}_2$.

Indeed, consider the polynomial ring $\mathbb{F}_2[k_1, \ldots, k_{128}]$ where each variable $k_i$ corresponds to a bit of the AES key. Then, we follow the operations performed by the evaluator in `BinaryCircuit.eval` like so:
- **Garbler's input wires:** for each garbler's input wire index `w` corresponding to the $i$-th bit of the AES key, we set its value $v_w = k_i$;
- **Evaluator's input wires:** for each evaluator's input wire index `w`, we set $v_w$ as its actual bit chosen by the evaluator;
- **XOR gates:** for each XOR gate with input wires indexes `a` and `b` and output wire index `c`, we set $v_c = v_a + v_b$;
- **NOT gates:** for each NOT gate with input wire index `a` and output wire index `b`, we set $v_b = v_a + 1$;
- **AND gates:** for each AND gate with input wires indexes `a` and `b` and output wire index `c`, we leak, using the global difference `D`, the actual values $a', b' \in \mathbb{F}_2$ of wires `a` and `b` and set $v_c = a' \cdot b'$; then we add the equations $v_a = a'$ and $v_b = b'$ to our system.

After evaluating all gates, we end up with a system of linear equations in the variables $k_1, \ldots, k_{128}$. Solving this system over $\mathbb{F}_2$ reveals the AES key used by the server. See the actual implementation in [solve.py](./src/solve.py) for more details.
