// 7e. Distinct patterns found per method. Per-detection precision rewards
// finding the same pattern many times: cycles_basic's 1,852 matched
// detections cover only 164 patterns (long loops through large, dense
// patterns). Detections per pattern found = detections / distinctPatterns.
// Expected: cycles_basic 164 (54 CYCLE), cycles_temporal 158 (49),
//   cycles_time_amount 153 (49), fan_out_daily 10, fan_in_daily 20.
MATCH (d:Detection)-[:MATCHES]->(p:Pattern)
RETURN d.method AS method, count(DISTINCT p) AS distinctPatterns,
       count(DISTINCT CASE WHEN p.type = 'CYCLE' THEN p END) AS cyclePatterns
ORDER BY method
