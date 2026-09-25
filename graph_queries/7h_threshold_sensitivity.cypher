// 7h. Matched detections at other Jaccard thresholds (nothing stored).
// Expected (0.3 / 0.5 / 0.7): cycles_basic 3,936 / 1,852 / 203;
//   cycles_temporal 200 / 108 / 65; cycles_time_amount 63 / 61 / 52;
//   fan_out_daily 45 / 10 / 0; fan_in_daily 60 / 20 / 1.
MATCH (d:Detection)<-[:MEMBER_OF]-(a:Account)-[:IN_PATTERN]->(p:Pattern)
WITH d, p, count(DISTINCT a) AS overlap
WITH d, max(toFloat(overlap) / (d.size + p.size - overlap)) AS best
RETURN d.method AS method,
       count(CASE WHEN best >= 0.3 THEN 1 END) AS at03,
       count(CASE WHEN best >= 0.5 THEN 1 END) AS at05,
       count(CASE WHEN best >= 0.7 THEN 1 END) AS at07
ORDER BY method
