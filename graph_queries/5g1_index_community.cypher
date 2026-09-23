// 5g. Index from the Review 1 schema.
CREATE INDEX account_community IF NOT EXISTS FOR (a:Account) ON (a.communityId);
