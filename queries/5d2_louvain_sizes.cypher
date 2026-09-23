// 5d. Largest communities.
MATCH (a:Account)
RETURN a.communityId AS community, count(*) AS size
ORDER BY size DESC LIMIT 20
