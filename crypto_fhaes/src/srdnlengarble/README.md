# srdnlengarble

Just a Python implementation of garbled circuits. Internally it functions similarly to the Rust library [fancy-garbling](https://github.com/GaloisInc/swanky/tree/dev/edge/fancy-garbling) with the same garbling methods. Additionally, it enables easy just-in-time circuit construction thanks to the classes in [wires](./wires) and [circuits](./circuits). 

In practice, one could use this library to build custom circuits, save them to a file using `BinaryCircuit.save`, and then use fancy-garbling to garble and evaluate them efficiently. So this library is mainly for ease of use (and avoid the :crab: rave).
