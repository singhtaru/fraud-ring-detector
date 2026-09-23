// 5e. Largest components. Expect one giant component plus many tiny ones;
// the 92,354 self-transfer-only accounts are singleton components.
MATCH (a:Account)
RETURN a.componentId AS component, count(*) AS size
ORDER BY size DESC LIMIT 10
