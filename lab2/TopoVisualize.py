import networkx as nx
import matplotlib.pyplot as plt

class TopoVisualize:

	def __init__(self):
		self.graph = [] # save edges
	
	def addEdge(self, e):
		self.graph.append(e)

	def draw(self):
		G = nx.Graph()
		G.add_edges_from(self.graph)
		nx.draw_networkx(G)
		plt.show()