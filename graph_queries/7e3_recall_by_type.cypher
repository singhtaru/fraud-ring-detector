// 7e. Recall per pattern type, all methods combined.
// Expected: BIPARTITE 21/49, CYCLE 54/54, FAN-IN 15/40, FAN-OUT 18/48,
//   GATHER-SCATTER 18/51, RANDOM 16/41, SCATTER-GATHER 33/44, STACK 14/43.
// Types other than the methods' targets are "found" only by overlap (rings or
// fans that share half their accounts with, e.g., a scatter-gather pattern).
