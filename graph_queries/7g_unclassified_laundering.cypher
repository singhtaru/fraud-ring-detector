// 7g. Laundering-involved accounts in no labelled pattern. Excluded from
// structure-level scoring (7d-7e): with no pattern there is nothing to match.
// Expected: 3,187 of the 6,357 laundering-involved accounts.
MATCH (a:Account)
WHERE a.evalLaunderingInvolved AND NOT EXISTS { (a)-[:IN_PATTERN]->() }
RETURN count(a) AS unclassifiedLaunderingAccounts
