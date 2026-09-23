// 5i. Done when this returns 0: every account has all three GDS properties.
MATCH (a:Account)
WHERE a.pageRank IS NULL OR a.communityId IS NULL OR a.componentId IS NULL
RETURN count(a)
