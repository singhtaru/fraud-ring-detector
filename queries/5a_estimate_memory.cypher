// 5a. Memory estimate for projecting the graph (native estimate; includes
// self-loops, so it slightly overstates the filtered projections in 5b).
// Proceed if requiredMemory is well below the 4G heap.
CALL gds.graph.project.estimate('Account', 'SENT')
YIELD requiredMemory, bytesMax
