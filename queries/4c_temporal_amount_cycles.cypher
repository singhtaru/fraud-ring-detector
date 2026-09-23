// 4c. Temporal cycles with amount conservation (each hop passes on 50-120%
// of the previous hop's value, in USD).
// Dedup: a time-ordered cycle has only one valid starting point, so the
// temporal check already stops a ring being counted once per member. The
// lowest-accountId rule only breaks ties when every hop has the same
// timestamp. (Applying it unconditionally would drop ~2/3 of real rings:
// only 17 of the 54 ground-truth cycles are time-ordered from their
// lowest-ID account, versus 49 from their true origin.)
// Amounts are converted to USD before comparing hops: 38 of 54 ground-truth
// cycles change currency mid-ring. Rates come from fx_rates.py. The band
// 0.5-1.2 keeps 52/54 real cycles (0.7-1.1 on raw amountPaid keeps 16/54).
WITH {`Australian Dollar`: 0.707814, `Bitcoin`: 11874.4, `Brazil Real`: 0.177101, `Canadian Dollar`: 0.757978, `Euro`: 1.17178, `Mexican Peso`: 0.0472968, `Ruble`: 0.0128528, `Rupee`: 0.0136158, `Saudi Riyal`: 0.266588, `Shekel`: 0.296121, `Swiss Franc`: 1.0929, `UK Pound`: 1.29166, `US Dollar`: 1, `Yen`: 0.00948767, `Yuan`: 0.149307} AS fx
MATCH path = (a:Account) ((x)-[r:SENT]->(y) WHERE x <> y){2,8} (a)
WHERE all(i IN range(0, size(r)-2) WHERE r[i].timestamp <= r[i+1].timestamp
        AND r[i+1].amountPaid * fx[r[i+1].paymentCurrency] > r[i].amountPaid * fx[r[i].paymentCurrency] * 0.5
        AND r[i+1].amountPaid * fx[r[i+1].paymentCurrency] < r[i].amountPaid * fx[r[i].paymentCurrency] * 1.2)
  AND (r[0].timestamp < r[-1].timestamp
       OR all(n IN nodes(path) WHERE a.accountId <= n.accountId))
RETURN path LIMIT 25
