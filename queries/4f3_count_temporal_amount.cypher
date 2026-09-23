// 4f (3/3). Count temporal cycles with USD amount conservation (as 4c).
// {2,5} because counting explores the whole graph. If it runs past ~3 min,
// stop it, change to {2,4} in all three 4f files, and note the range used.
WITH {`Australian Dollar`: 0.707814, `Bitcoin`: 11874.4, `Brazil Real`: 0.177101, `Canadian Dollar`: 0.757978, `Euro`: 1.17178, `Mexican Peso`: 0.0472968, `Ruble`: 0.0128528, `Rupee`: 0.0136158, `Saudi Riyal`: 0.266588, `Shekel`: 0.296121, `Swiss Franc`: 1.0929, `UK Pound`: 1.29166, `US Dollar`: 1} AS fx
MATCH path = (a:Account) ((x)-[r:SENT]->(y) WHERE x <> y){2,5} (a)
WHERE all(i IN range(0, size(r)-2) WHERE r[i].timestamp <= r[i+1].timestamp
        AND r[i+1].amountPaid * fx[r[i+1].paymentCurrency] > r[i].amountPaid * fx[r[i].paymentCurrency] * 0.5
        AND r[i+1].amountPaid * fx[r[i+1].paymentCurrency] < r[i].amountPaid * fx[r[i].paymentCurrency] * 1.2)
  AND (r[0].timestamp < r[-1].timestamp
       OR all(n IN nodes(path) WHERE a.accountId <= n.accountId))
RETURN count(path) AS cycles,
       sum(CASE WHEN all(rel IN relationships(path) WHERE rel.isLaundering = 1)
                THEN 1 ELSE 0 END) AS launderingCycles
