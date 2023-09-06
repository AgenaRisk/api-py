from .node import Node

import networkx as nx
import matplotlib.pyplot as plt

class Network():
    def __init__(self, id, name=None, description=None, nodes=None):
            
        self.id = id

        if name is None:
            self.name = self.id
        else:
            self.name = name
        
        if description is None:
            self.description = "New Network"
        else:
            self.description = description
        
        if nodes is not None:
            self.nodes = nodes
        else:
            self.nodes = []
        
    def plot(self):

        from_list = []
        to_list = []

        for nd in self.nodes:
            if len(nd.parents)>0:
                for pr in nd.parents:
                    from_list.append(pr.id)
                    to_list.append(nd.id)
        
        G = nx.DiGraph()
        for nd in self._get_nodes():
            G.add_node(nd)

        for p, c in zip(from_list, to_list):
            G.add_edges_from([(p, c)])

        nx.draw(G,with_labels=True)
        plt.draw()
        plt.show()

    def add_node(self, new_node: Node):
        if new_node.id in self._get_nodes():
            raise ValueError("There is already a node in the network with this id")
        else:
            self.nodes.append(new_node)
            print(f"The node {new_node.name} is successfully added to the network. If {new_node.name} has any parent nodes, make sure to add them to the network separately")

    def remove_node(self, old_node: Node):  
        if old_node in self.nodes:
            self.nodes.remove(old_node)
            print(f"The node {old_node.name} is successfully removed from the network. If {old_node.name} had any child nodes in the network, make sure to adjust their parents accordingly")
        else:
            raise ValueError("This node is not in the network")

    def _get_nodes(self):
        nodes_list = []
        if len(self.nodes)>0:
            for nd in self.nodes:
                nodes_list.append(nd.id)
            
        return nodes_list
    
    def get_node(self, node_id):
          if node_id not in self._get_nodes():
               raise ValueError(f"The model does not have a dataset with the id {node_id}")
          
          node = [n for n in self.nodes if n.id==node_id].pop()
          return node
    
    def __str__(self) -> str:
        if self.nodes is not None:
            return  "Network id: % s\nNetwork name: % s\nNetwork nodes: % s" % (self.id, self.name, ", ".join(self._get_nodes()))
        else:
            return  "Network id: % s\nNetwork name: % s" % (self.id, self.name)        

    def __repr__(self) -> str:
        return "Bayesian Network: % s (% s)" % (self.name, ", ".join(self._get_nodes())) 
