"""Convert all of HI-Small_Trans.csv into transactions.csv for LOAD CSV.

Same row format as prep_slice.py (shared via to_output_row).
"""
import csv
import time

from prep_slice import OUT_COLUMNS, to_output_row

start = time.time()
written = 0
with open("data/HI-Small_Trans.csv", newline="") as src, \
     open("transactions.csv", "w", newline="") as dst:
    reader = csv.reader(src)
    next(reader)  # original header has duplicate "Account" columns; replace it
    writer = csv.writer(dst)
    writer.writerow(OUT_COLUMNS)

    for i, values in enumerate(reader):
        row = to_output_row(i, values)
        writer.writerow(row[c] for c in OUT_COLUMNS)
        written += 1
        if written % 1_000_000 == 0:
            print(f"{written:,} rows...")

print(f"Wrote {written:,} rows to transactions.csv in {time.time() - start:.0f}s")
