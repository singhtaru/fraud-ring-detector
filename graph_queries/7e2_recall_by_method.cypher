// 7e. Recall per method, for the method's target type only.
// Expected: cycles_basic 54/54, cycles_temporal 49/54, cycles_time_amount 49/54,
//           fan_out_daily 2/48 (FAN-OUT), fan_in_daily 4/40 (FAN-IN).
UNWIND [['cycles_basic', 'CYCLE'], ['cycles_temporal', 'CYCLE'],
        ['cycles_time_amount', 'CYCLE'], ['fan_out_daily', 'FAN-OUT'],
        ['fan_in_daily', 'FAN-IN']] AS mt
MATCH (p:Pattern {type: mt[1]})
RETURN mt[0] AS method, mt[1] AS type, count(p) AS labelled,
       count(CASE WHEN EXISTS { (p)<-[:MATCHES]-(:Detection {method: mt[0]}) } THEN 1 END) AS recalled
