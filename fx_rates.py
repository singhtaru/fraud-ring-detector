"""Derive USD exchange rates from the dataset itself and print a Cypher map.

For every transaction paid in US Dollars but received in another currency,
amountReceived / amountPaid is that day's rate; the median per currency is
used. The printed map is pasted into the amount-conservation queries
(queries/4c_*.cypher, queries/4f3_*.cypher) so amounts in different
currencies can be compared hop to hop.
"""
import csv
import statistics
from collections import defaultdict

rates = defaultdict(list)
with open("data/HI-Small_Trans.csv", newline="") as f:
    reader = csv.reader(f)
    next(reader)
    for v in reader:
        received, recv_cur, paid, pay_cur = float(v[5]), v[6], float(v[7]), v[8]
        if pay_cur == "US Dollar" and recv_cur != "US Dollar" and paid > 0:
            rates[recv_cur].append(received / paid)

usd_per_unit = {"US Dollar": 1.0}
for cur, values in rates.items():
    usd_per_unit[cur] = 1 / statistics.median(values)

print("{" + ", ".join(f"`{c}`: {r:.6g}" for c, r in sorted(usd_per_unit.items())) + "}")
