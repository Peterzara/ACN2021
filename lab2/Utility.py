from topo import Edge, Node


def _findMinVertex(dist, sptSet):
    min = 0x3f3f3f3f

    for d in range(len(dist)):
        if dist[d] < min and sptSet[d] is False:
            min = dist[d]
            minIndex = d
    return minIndex

def dijstra(src, graph, hostList):
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
    for host in hostList:
        if host == src: # discard itself
            continue
        idx = graph.index(host)
        path.append(dist[idx])
    return path

