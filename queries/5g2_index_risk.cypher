// 5g. Index from the Review 1 schema (riskScore is written in a later phase).
CREATE INDEX account_risk IF NOT EXISTS FOR (a:Account) ON (a.riskScore);
