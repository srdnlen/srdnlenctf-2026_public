from sage.crypto.sboxes import Ascon as S
import itertools

known_to_unknown = dict()
for x0, x1 in itertools.combinations(range(32), 2):
    dx = x0 ^ x1
    if dx & 0b11100 != 0:
        continue
    y0 = S(x0)
    y1 = S(x1)
    dy = y0 ^ y1
    known = (dx, x0 >> 4, x1 >> 4, x0 & 0b11, x1 & 0b11)
    if known not in known_to_unknown:
        known_to_unknown[known] = []
    unknown = (x0 >> 2 & 0b11, x1 >> 2 & 0b11, y0, y1, dy)
    known_to_unknown[known].append(unknown)

dxy_to_relation = dict()
for known, unknowns in known_to_unknown.items():
    dx, iv, iv_, n0, n1 = known
    assert iv == iv_
    print(f"dx={dx:05b}, iv={iv:b}, n0={n0:02b}, n1={n1:02b}:")
    for k, k_, y0, y1, dy in unknowns:
        assert k == k_
        print(f"  k={k:02b}  ==>  y0={y0:05b}, y1={y1:05b}, dy={dy:05b}")
        if (dx, dy) not in dxy_to_relation:
            dxy_to_relation[(dx, dy)] = []
        dxy_to_relation[(dx, dy)].append((iv, n0, n1, k))
print()

for (dx, dy), relations in dxy_to_relation.items():
    print(f"dx={dx:05b}, dy={dy:05b}:")
    for i, n0, n1, k in relations:
        print(f"  iv={i:b}, n0={n0:02b}, n1={n1:02b}  ==>  k={k:02b}")
print()
