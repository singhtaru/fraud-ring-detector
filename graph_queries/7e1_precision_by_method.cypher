// 7e. Precision per method = detections matching any pattern / detections.
// Expected (detections / matched):
//   cycles_basic 8,477 / 1,852    cycles_temporal 4,187 / 108
//   cycles_time_amount 1,226 / 61    fan_out_daily 49,765 / 10    fan_in_daily 6,516 / 20
MATCH (d:Detection)
RETURN d.method AS method, d.target AS target, count(d) AS detections,
       count(CASE WHEN EXISTS { (d)-[:MATCHES]->() } THEN 1 END) AS matched
ORDER BY method
