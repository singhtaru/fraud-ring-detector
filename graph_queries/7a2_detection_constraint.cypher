// 7a. Unique detection keys (also the index the 7b/7c MERGEs look up).
CREATE CONSTRAINT detection_key IF NOT EXISTS
FOR (d:Detection) REQUIRE d.key IS UNIQUE;
