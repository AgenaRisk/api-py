import logging

class Node():

    def __init__(self, id, name=None, description=None, type=None, simulated=None, states=None):
        
        # initiating a new object with the id
        self.id = str(id)
        self.parents = [] #all nodes are created with an empty list of parents
        self.variables = []

        # assigning name and description
        if name is None:
             self.name = id
        else:
             self.name = str(name)

        if description is None:
             self.description = "New Node"
        else:
             self.description = str(description)
        
        # first check if the node is simulated or not, then get type and states information, use sensible defaults when not given
        if simulated is None or simulated==False:
            self.simulated = False
            if type is None:
                self.type = "Boolean"
                if states is None:
                    self.states = ["False", "True"]
                else:
                    if len(states)==2:
                        self.states = states
                    else:
                        self.states = ["False", "True"]
            else:
                self.type = type
                if self.type == "Labelled":
                    if states is None:
                        self.states = ["False", "True"]
                    else:
                        self.states = states
                if self.type == "Ranked":
                    if states is None:
                        self.states = ["Low", "Medium", "High"]
                    else:
                        self.states = states
                if self.type == "DiscreteReal":
                    if states is None:
                        self.states = ["0.0", "1.0"]
                    else:
                        self.states = states
                if self.type == "ContinuousInterval":
                    if states is None:
                        self.states = ["(-Infinity, -1)", "[-1, 1)", "[1, Infinity)"]
                    else:
                        self.states = states
                if self.type == "IntegerInterval":
                    if states is None:
                        self.states = ["(-Infinity, -1]", "[0, 4]"," [5, Infinity)"]
                    else:
                        self.states = states                
                if self.type == "Boolean":
                    if states is None:
                        self.states = ["False", "True"]
                    else:
                        if len(states)==2:
                            self.states = states
                        else:
                            self.states = ["False", "True"]
        else:
            self.simulated = True
            self.states = None
            if type is None:
                self.type = "ContinuousInterval" 
            else:             
                if type == "IntegerInterval":
                    self.type = type
                else:
                    self.type = "ContinuousInterval"    

        # create distribution type, probabilities, and expressions fields and fill in with sensible defaults
        # these fields will have class methods to rewrite
        if self.simulated:
            self.distr_type = "Expression"
            self.expressions = "Normal(0,1000000)"
            self.probabilities = None
        else:
            if (self.type == "ContinuousInterval" or self.type == "IntegerInterval"):
                self.distr_type = "Expression"
                self.expressions = "Normal(0,1000000)"
                self.probabilities = None
            else:
                self.distr_type = "Manual"
                self.probabilities = [[1/len(self.states)] * len(self.states)]
                self.expressions = None
        
    @property
    def type(self):
        return self.__type
    
    @type.setter
    def type(self, value):
        if value is not None and value not in ["Boolean", "Labelled", "Ranked", "DiscreteReal", "ContinuousInterval", "IntegerInterval"]:
            raise ValueError("Invalid node type")
        
        self.__type = value

    def __str__(self) -> str:
        if self.states is not None:
            return  "Node id: % s\nNode name: % s\nNode type: % s\nNode states: % s" % (self.id, self.name, self.type, ", ".join(self.states))
        else:
            return  "Node id: % s\nNode name: % s\nNode type: % s" % (self.id, self.name, self.type)

    def __repr__(self) -> str:
        if self.simulated:
            return "Simulated node: % s (% s)" % (self.name, self.type) 
        else:
            return "Node: % s (% s)" % (self.name, self.type)
    

    def set_states(self, states, from_cmpx=False):
        
        previous_states = len(self.states)

        self.states = states
        if len(self.states) != previous_states:
            self._reset_probabilities()
            if not from_cmpx:
                logging.info("The node states are updated, the NPT values are reset to uniform because the number of states has changed")
        else:
            if not from_cmpx:
                logging.info("The node states are updated")
            
    def add_parent(self, new_parent: "Node", from_cmpx=False):

        if new_parent.id == self.id:
            raise ValueError("You cannot add a node as a parent to itself")

        parent_ids = []
        if len(self.parents)>0:
            for pr in self.parents:
                parent_ids.append(pr.id)
        
        if new_parent.id in parent_ids:
            raise ValueError("The parent already exists")
        else:
            self.parents.append(new_parent)
        
        if self.distr_type == "Manual":
            if new_parent.distr_type == "Manual":
                self._reset_probabilities()
                if not from_cmpx:
                    logging.info(f"The node {new_parent.name} has been added to the parents of {self.name} and NPT values are reset to uniform")
            else:
                self.set_distr_type("Expression", from_cmpx=from_cmpx)
                if not from_cmpx:
                    logging.info(f"The node {new_parent.name} has been added to the parents of {self.name} and distribution (table) type of {self.name} is changed to expression")
        else:
            if not from_cmpx:
                logging.info(f"The node {new_parent.name} has been added to the parents of {self.name} and now can be used in its expression")

    def _addparentbyID(self, parentslist: list, parentid: str):
        par = [pr for pr in parentslist if pr.id==parentid].pop()
        self.add_parent(par, from_cmpx=True)

    def remove_parent(self, old_parent: "Node"):
        if old_parent in self.parents:
            self.parents.remove(old_parent)

        if self.distr_type == "Manual":
            self._reset_probabilities()
            logging.info(f"The node {old_parent.name} has been removed from the parents of {self.name} and NPT values are reset to uniform")
        else:
            self.expressions = "Normal(0,1000000)"
            logging.info(f"The node {old_parent.name} has been removed from the parents of {self.name} and the expression has been reset to default")

    # A function to reset the manual NPTs to default uniform when a parent is added or removed
    def _reset_probabilities(self):
        temp_length = 1
        if len(self.parents)>0:
            for pr in self.parents:
                temp_length *= len(pr.states)
        
        self.probabilities = [[1/len(self.states)] * len(self.states)] * temp_length

    def set_probabilities(self, probabilities, by_row=False, from_cmpx = False):
        
        if not by_row:
            if not self.simulated:
                if (self.distr_type == "Manual") or (self.type=="ContinuousInterval" and self.states is not None) or (self.type=="IntegerInterval" and self.states is not None):
                    if not from_cmpx:
                        temp_length = 1
                        subset_length_control = 1
                        if len(self.parents)>0:
                            for pr in self.parents:
                                if pr.states is not None:
                                    temp_length *= len(pr.states)
                    
                        for ss in probabilities:
                            if len(ss)==len(self.states):
                                subset_length_control *= 1
                            else:
                                subset_length_control *= 0
                    
                        if (len(probabilities) == temp_length) & (subset_length_control==1):
                            self.probabilities = probabilities
                        else:
                            raise ValueError("The number of probabilities does not match the size of node NPT")
                    else:
                        self.probabilities = probabilities

            else:
                raise ValueError(f"The node {self.id} does not have a manual NPT")

        if by_row:
            if not self.simulated:
                if (self.distr_type == "Manual") or (self.type=="ContinuousInterval" and self.states is not None) or (self.type=="IntegerInterval" and self.states is not None):
                    if not from_cmpx:
                        temp_length = 1
                        subset_length_control = 1
                        if len(self.parents)>0:
                            for pr in self.parents:
                                if pr.states is not None:
                                    temp_length *= len(pr.states)

                        if (self.type != "ContinuousInterval") or (self.type != "IntegerInterval"):
                            for ss in probabilities:
                                if len(ss)==temp_length:
                                    subset_length_control *= 1
                                else:
                                    subset_length_control *= 0
                    
                        if (len(probabilities) == len(self.states)) & (subset_length_control==1):
                            self.probabilities = list(map(list, zip(*probabilities)))
                        else:
                            raise ValueError("The number of probabilities does not match the size of node NPT")
                    else:
                        self.probabilities = list(map(list, zip(*probabilities)))
            else:
                raise ValueError(f"The node {self.id} does not have a manual NPT")

    def _get_parents(self):
        par_list = []
        if len(self.parents)>0:
            for pr in self.parents:
                par_list.append(pr.id)
        return par_list

    def set_expressions(self, expressions, partitioned_parents=None, from_cmpx=False):
        self.expressions = expressions
        
        if (partitioned_parents is None) & (self.distr_type == "Manual"):
            self.set_distr_type("Expression", from_cmpx=from_cmpx)

        if partitioned_parents is not None:
            if set(partitioned_parents).issubset(set(self._get_parents())):
                self.partitions = partitioned_parents
                self.set_distr_type("Partitioned", from_cmpx=from_cmpx)
            else:
                self.expressions = None
                raise ValueError(f"One or more given partition parents is not a parent of the node {self.name}")

    def _get_variable_names(self):
        var_names = []
        if len(self.variables)>0:
            for vr in self.variables:
                (k, v), = vr.items()
                var_names.append(k)
        
        return var_names
    
    def _get_variable_value(self, variable_name):
        if len(self.variables)>0:
            for vr in self.variables:
                (k, v), = vr.items()
                if k == variable_name:
                    variable_value = v
        
        return variable_value

    def set_variable(self, variable_name, variable_value, from_cmpx=False):
        if variable_name in self._get_variable_names():
            raise ValueError("The node already has a variable (constant) with this name")
        else:
            self.variables.append({variable_name:variable_value})
            if not from_cmpx:
                logging.info("The variable (constant) is successfully added to the node")

    def remove_variable(self, variable_name):
        if variable_name in self._get_variable_names():
            for ix, vr in enumerate(self.variables):
                (k, v), = vr.items()
                if k == variable_name:
                    self.variables.pop(ix)
            logging.info("The variable (constant) is removed from the node")
        else:
            raise ValueError(f"The node does not have a variable called {variable_name}")

    def set_distr_type(self, distr_type, from_cmpx=False):
        self.distr_type = distr_type

        if self.distr_type=="Manual":
            self.partitions = None
            self.expressions = None
            self._reset_probabilities()
            if not from_cmpx:
                logging.info("The node's distribution type is converted to a manual table and a default NPT is assigned")
        
        if (self.distr_type=="Expression") | (self.distr_type=="Partitioned"):
            self.probabilities = None
            if self.expressions == None:
                self.expressions = "Normal(0,1000000)"
                if not from_cmpx:
                    logging.info("The node's distribution type is converted to expression (or partitioned) and a default expression is assigned")
            else:
                if not from_cmpx:
                    logging.info("The node's distribution type is converted to expression (or partitioned)")


    @property
    def distr_type(self):
        return self.__distr_type
    
    @distr_type.setter
    def distr_type(self, value):
        if value is not None and value not in ["Manual", "Expression", "Partitioned"]:
            raise ValueError("Invalid distribution (table) type - it should be Manual, Expression, or Partitioned")
        
        if (value=="Partitioned") & (len(self.parents)==0):
            raise ValueError("The node has no parents, it cannot have a partitioned expression")
        
        if (value=="Manual") & (self.simulated):
            raise ValueError("Simulation nodes cannot have a manual table definition")

        self.__distr_type = value


    @property
    def type(self):
        return self.__type
    
    @type.setter
    def type(self, value):
        if value is not None and value not in ["Boolean", "Labelled", "Ranked", "DiscreteReal", "ContinuousInterval", "IntegerInterval"]:
            raise ValueError("Invalid node type")
        
        self.__type = value