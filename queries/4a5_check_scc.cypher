// 4a (check). Largest SCCs. Expect 17,075 then several of ~11-12 accounts.
MATCH (a:Account)
WITH a.sccId AS scc, count(*) AS size
WHERE size > 1
RETURN count(scc) AS multiAccountSCCs, sum(size) AS accountsInThem,
       max(size) AS largest
