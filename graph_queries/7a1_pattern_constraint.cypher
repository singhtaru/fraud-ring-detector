// 7a. Phase 7 setup: unique pattern ids.
CREATE CONSTRAINT pattern_id IF NOT EXISTS
FOR (p:Pattern) REQUIRE p.patternId IS UNIQUE;
