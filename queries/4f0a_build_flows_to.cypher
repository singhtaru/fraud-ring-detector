// 4f (setup 1/4). Build one FLOWS_TO relationship per (sender, receiver) pair,
// rolling up all SENT transactions between them (self-transfers excluded).
//
// Why: 4.49M non-self SENT rels connect only 647,939 distinct pairs (6.9 per
// pair). Counting cycles over SENT walks every combination of parallel
// transactions (up to 6.9^k per ring) and never finishes; over FLOWS_TO the
// full {2,12} ring search is ~38M expansions.
//
// Lists are ordered by time and aligned by index:
//   ts[j] = timestamp, usd[j] = amountPaid in USD (rates: fx_rates.py),
//   laund[j] = isLaundering
// MERGE makes this safe to re-run. Expect 647,939 FLOWS_TO relationships.
:auto MATCH (a:Account)
CALL (a) {
  WITH {`Australian Dollar`: 0.707814, `Bitcoin`: 11874.4, `Brazil Real`: 0.177101, `Canadian Dollar`: 0.757978, `Euro`: 1.17178, `Mexican Peso`: 0.0472968, `Ruble`: 0.0128528, `Rupee`: 0.0136158, `Saudi Riyal`: 0.266588, `Shekel`: 0.296121, `Swiss Franc`: 1.0929, `UK Pound`: 1.29166, `US Dollar`: 1, `Yen`: 0.00948767, `Yuan`: 0.149307} AS fx
  MATCH (a)-[r:SENT]->(b:Account)
  WHERE a <> b
  WITH a, b, r, fx ORDER BY r.timestamp
  WITH a, b, collect(r.timestamp) AS ts,
       collect(r.amountPaid * fx[r.paymentCurrency]) AS usd,
       collect(r.isLaundering) AS laund
  MERGE (a)-[f:FLOWS_TO]->(b)
  SET f.ts = ts, f.usd = usd, f.laund = laund, f.txCount = size(ts)
} IN TRANSACTIONS OF 2000 ROWS
