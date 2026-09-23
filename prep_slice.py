"""Prepare a slice of HI-Small_Trans.csv for LOAD CSV into Neo4j.

The slice = the first NROWS transactions + every transaction that belongs to
a CYCLE laundering pattern in HI-Small_Patterns.txt. Cycle transactions are
spread across the whole 5M-row file (and over several days), so a plain
head-of-file slice contains no complete cycle; adding them guarantees one.

transactionId is the row's index in the full CSV, so IDs stay stable when
the full dataset is loaded later.

Uses only the standard library (pandas' compiled DLLs are blocked by
Windows Application Control on this machine). All values stay strings,
so hex account IDs like 8000EBD30 are never coerced to numbers.

Usage: python prep_slice.py [NROWS]
"""
import csv
import sys
from datetime import datetime

COLUMNS = ["timestamp", "fromBank", "fromAccount", "toBank", "toAccount",
           "amountReceived", "receivingCurrency", "amountPaid",
           "paymentCurrency", "paymentFormat", "isLaundering"]
OUT_COLUMNS = COLUMNS + ["fromId", "toId", "transactionId"]


def to_output_row(i, values):
    """Turn the raw CSV values of row i into the dict written for LOAD CSV."""
    row = dict(zip(COLUMNS, values))

    # Dataset uses "2022/09/01 00:20" — convert to ISO so Neo4j's datetime() accepts it
    row["timestamp"] = datetime.strptime(row["timestamp"], "%Y/%m/%d %H:%M") \
                               .strftime("%Y-%m-%dT%H:%M:%S")

    # Composite IDs: same account number can exist at different banks.
    # Bank codes are kept verbatim: both files use the same zero-padded
    # strings, and int()-normalising would merge codes like 039198/0039198.
    row["fromId"] = row["fromBank"] + "_" + row["fromAccount"]
    row["toId"] = row["toBank"] + "_" + row["toAccount"]
    row["transactionId"] = str(i)
    return row


def main():
    nrows = int(sys.argv[1]) if len(sys.argv) > 1 else 50000

    # Collect the raw lines of every CYCLE pattern
    cycle_lines = set()
    in_cycle = False
    with open("data/HI-Small_Patterns.txt") as f:
        for line in f:
            line = line.strip()
            if line.startswith("BEGIN LAUNDERING ATTEMPT"):
                in_cycle = "CYCLE" in line
            elif line.startswith("END LAUNDERING ATTEMPT"):
                in_cycle = False
            elif in_cycle and line:
                cycle_lines.add(line)

    written = head_rows = cycle_rows = 0
    matched_cycle_lines = set()
    missing = {c: 0 for c in OUT_COLUMNS}

    with open("data/HI-Small_Trans.csv", newline="") as src, \
         open("slice.csv", "w", newline="") as dst:
        next(src)  # original header has duplicate "Account" columns; replace it
        writer = csv.writer(dst)
        writer.writerow(OUT_COLUMNS)

        for i, line in enumerate(src):
            raw = line.strip()
            in_head = i < nrows
            is_cycle = raw in cycle_lines
            if not (in_head or is_cycle):
                continue
            if is_cycle:
                matched_cycle_lines.add(raw)
                if not in_head:
                    cycle_rows += 1
            if in_head:
                head_rows += 1

            row = to_output_row(i, next(csv.reader([raw])))
            for c in OUT_COLUMNS:
                if not row.get(c):
                    missing[c] += 1
            writer.writerow(row[c] for c in OUT_COLUMNS)
            if written < 5:
                print(row)
            written += 1

    print(f"\nHead rows:            {head_rows}")
    print(f"Extra cycle rows:     {cycle_rows}")
    print(f"Total rows written:   {written}  -> slice.csv")
    print(f"Cycle pattern lines:  {len(cycle_lines)} "
          f"({len(cycle_lines - matched_cycle_lines)} not found in Trans.csv)")
    print("Empty values per column:", missing)


if __name__ == "__main__":
    main()
