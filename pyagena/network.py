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

    def create_node(self, id, name=None, description=None, type=None, simulated=None, states=None):
        this_node = Node(id=id, name=name, description=description, type=type, simulated=simulated, states=states)
        self.add_node(this_node)

    def create_edge(self, child, parent):
        child_node = self.get_node(child)
        parent_node = self.get_node(parent)
        child_node.add_parent(parent_node)

    def set_node_probabilities(self, node_id, new_probs, by_row=False):
        node = self.get_node(node_id)
        node.set_probabilities(new_probs=new_probs, by_row=by_row)

    def set_node_states(self, node_id, states):
        node = self.get_node(node_id)
        node.set_states(states)

    def set_node_expressions(self, node_id, expressions, partitioned_parents=None, from_cmpx=False):
        node = self.get_node(node_id)
        node.set_expressions(expressions=expressions, partitioned_parents=partitioned_parents, from_cmpx=from_cmpx)
    
    def set_node_variable(self, node_id, variable_name, variable_value, from_cmpx=False):
        node = self.get_node(node_id)
        node.set_variable(variable_name=variable_name, variable_value=variable_value, from_cmpx=from_cmpx)

    def set_node_distr_type(self, node_id, distr_type, from_cmpx=False):
        node = self.get_node(node_id)
        node.set_distr_type(distr_type=distr_type, from_cmpx=from_cmpx)

    def add_node(self, new_node: Node):
        if new_node.id in self._get_nodes():
            raise ValueError("There is already a node in the network with this id")
        else:
            self.nodes.append(new_node)
            print(f"The node {new_node.name} is successfully added to the network. If {new_node.name} has any parent nodes, make sure to add them to the network separately")

    def remove_node(self, node_id):  
        old_node = self.get_node(node_id)
        if old_node in self.nodes:
            self.nodes.remove(old_node)
            print(f"The node {node_id} is successfully removed from the network. If {node_id} had any child nodes in the network, make sure to adjust their parents accordingly")
        else:
            raise ValueError("This node is not in the network")

    def _get_nodes(self):
        nodes_list = []
        if len(self.nodes)>0:
            for nd in self.nodes:
                nodes_list.append(nd.id)
            
        return nodes_list
    
    def get_node(self, node_id) -> Node:
          if node_id not in self._get_nodes():
               raise ValueError(f"The model does not have a node with the id {node_id}")
          
          node = [n for n in self.nodes if n.id==node_id].pop()
          return node
    
    def __str__(self) -> str:
        if self.nodes is not None:
            return  "Network id: % s\nNetwork name: % s\nNetwork nodes: % s" % (self.id, self.name, ", ".join(self._get_nodes()))
        else:
            return  "Network id: % s\nNetwork name: % s" % (self.id, self.name)        

    def __repr__(self) -> str:
        return "Bayesian Network: % s (% s)" % (self.name, ", ".join(self._get_nodes())) 
