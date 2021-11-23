import topo

# utility function
def _findMinVertex(dist, sptSet):
    min = 0x3f3f3f3f

    for d in range(len(dist)):
        if dist[d] < min and sptSet[d] is False:
            min = dist[d]
            minIndex = d
    return minIndex

# @Dijkstra: Calculate shortest path for each pair of server, and return a list of path length
# @src: source node
# @graph: a list composed of switch & server node
# @servers: a list of server
def Dijkstra(src, graph, servers):
    MAX = 0x3f3f3f3f
    vertices = len(graph)
    path = []

    dist = [MAX]*vertices
    srcIndex = graph.index(src)
    dist[srcIndex] = 0
    sptSet = [False]*vertices

    for i in range(vertices):
        currIndex = _findMinVertex(dist, sptSet)

        sptSet[currIndex] = True

        # update current node neighbors
        for adj in graph[currIndex].edges:
            adjIndex = graph.index(adj.rnode) # lnode is current node itself
            if dist[adjIndex] > 0 and sptSet[adjIndex] is False and dist[adjIndex] > dist[currIndex] + 1:
                # each edge weight is 1
                dist[adjIndex] = dist[currIndex] + 1


    # log host distance
    for server in servers:
        if server == src: # discard itself
            continue
        idx = graph.index(server)
        path.append(dist[idx])
    return path

