from .node import Node
from .network import Network
from .dataset import Dataset

import json
import pandas as pd
import os

class Model():         
     def __init__(self, networks:list[Network]=None, id=None, datasets=None, network_links=None, settings=None):
          
          if networks is not None:
               self.networks = networks
          else:
               self.networks = []

          if settings is None:
               self.settings = {"parameterLearningLogging":False, "discreteTails":False, "sampleSizeRanked":5, "convergence":0.01, "simulationLogging":False, "iterations":50, "tolerance":1}
          else:
               self.settings = settings

          if id is not None:
               self.id = id
          else:
               self.id = None

          if datasets is None:
               self.datasets = []
               self.datasets.append(Dataset(id="Case 1"))
          else:
               self.datasets = datasets

          if network_links is None:
               self.network_links = []
          else:
               self.network_links = network_links
          
     def __str__(self) -> str:
          if self.id is not None:
               return  "Model id: % s\nModel networks: % s" % (self.id, ", ".join(self._get_networks()))   
          else:
               return  "Model networks: % s" % (", ".join(self._get_networks()))   
     
     def __repr__(self) -> str:
          if self.id is not None:
               return "Bayesian Model: % s (% s)" % (self.id, ", ".join(self._get_networks())) 
          else:
               return "Bayesian Model: (% s)" % (", ".join(self._get_networks())) 

     def create_network(self, id, name=None, description=None):
          this_net = Network(id=id, name=name, description=description)
          self.add_network(this_net)

     def add_network(self, network):
          if network.id in self._get_networks():
               raise ValueError("There is already a network with this id in the model")
          else:
               self.networks.append(network)
               print("The network is successfully added to the model")

     def remove_network(self, id):
          network = self.get_network(id)
          if network not in self.networks:
               raise ValueError("This network is not in the model")
          else:
               self.networks.remove(network)
               print(f"The network is successfully removed from the model - if {network.id} had any links to other networks in the model, make sure to adjust network links accordingly")

     def _get_networks(self):
        nets_list = []
        if len(self.networks)>0:
            for nt in self.networks:
                nets_list.append(nt.id)
            
        return nets_list

     def get_network(self, network_id):
          if network_id not in self._get_networks():
               raise ValueError(f"The model does not have a network with the id {network_id}")
          
          network = [n for n in self.networks if n.id==network_id].pop()
          return network

     def get_dataset(self, dataset_id):
          if dataset_id not in self._get_datasets():
               raise ValueError(f"The model does not have a dataset with the id {dataset_id}")
              
          dataset = [d for d in self.datasets if d.id==dataset_id].pop()
          return dataset

     def add_network_link(self, source_network_id, source_node_id, target_network_id, target_node_id, link_type="Marginals", pass_state=None):
          out_nw = self.get_network(source_network_id)
          out_node = out_nw.get_node(source_node_id)
          in_nw = self.get_network(target_network_id)
          in_node = in_nw.get_node(target_node_id)

          if len(in_node.parents)>0:
               raise ValueError("The target node cannot be a node with parents in its network")
          
          #if in_node already a target_node raise error

          targets = []
          if len(self.network_links)>0:
               for nl in self.network_links:
                    targets.append(nl["targetNode"])
          
          if target_node_id in targets:
               raise ValueError("The required target node is already a target for an existing network link")

          num_list = ["ContinuousInterval", "IntegerInterval", "DiscreteReal"]
          num_intv_list = ["ContinuousInterval", "IntegerInterval"]
          valid = True

          if link_type == "Marginals":
               if not out_node.simulated and not in_node.simulated:
                    pass
               else:
                    if out_node.type in num_list and in_node.type in num_list:
                         pass
                    else:
                         valid = False

          if link_type in ["Mean", "Median", "Variance", "StandardDeviation", "LowerPercentile", "UpperPercentile"]:
               if out_node.type in num_list & in_node.simulated:
                    pass
               else:
                    valid = False

          if link_type == "State":
               if out_node.type not in num_intv_list and in_node.simulated:
                    pass
               else:
                    valid = False

          if valid:
               if link_type == "State":
                    if pass_state is None:
                         raise ValueError("Please enter the source node state to be passed on")
                    else:
                         new_link = {"sourceNode":source_node_id,
                                   "sourceNetwork":source_network_id,
                                   "targetNode":target_node_id,
                                   "targetNetwork":target_network_id,
                                   "passState":pass_state,
                                   "type":link_type}
               else:
                    new_link = {"sourceNode":source_node_id,
                                   "sourceNetwork":source_network_id,
                                   "targetNode":target_node_id,
                                   "targetNetwork":target_network_id,
                                   "type":link_type}
               
               self.network_links.append(new_link)
          else:
               raise ValueError("The link between source node and target node is not valid")                    

     def remove_network_link(self, source_network_id, source_node_id, target_network_id, target_node_id):

          if len(self.network_links)==0:
               raise ValueError("This model has no network links")
          
          link_to_remove = [nl for nl in self.network_links if nl["sourceNode"]==source_node_id and nl["sourceNetwork"]==source_network_id and nl["targetNode"]==target_node_id and nl["targetNetwork"]==target_network_id].pop()
          
          if link_to_remove in self.network_links:
               self.network_links.remove(link_to_remove)
               print("The network link is successfully removed from the model")
          else:
               raise ValueError("This network link does not exist in the model")

     def remove_all_network_links(self):
          self.network_links = []
          print("All network links are removed from the model")

     def create_dataset(self, dataset_id, from_cmpx=False):
          new_ds = Dataset(id=dataset_id)
          self.datasets.append(new_ds)
          if not from_cmpx:
               print("The dataset is successfully created")

     def remove_dataset(self, dataset_id, from_cmpx=False):
          if dataset_id not in self._get_datasets():
               raise ValueError("This dataset does not exist in the model")

          del_ds = self.get_dataset(dataset_id)
          self.datasets.remove(del_ds)
          if not from_cmpx:
               print("The dataset is successfully removed from the model")

     def _get_datasets(self):
          ds_list = []

          if len(self.datasets)>0:
               for ds in self.datasets:
                    ds_list.append(ds.id)
          
          return ds_list
     
     def enter_observation(self, network_id, node_id, value, dataset_id=None, variable_name=None):
          if dataset_id is None:
               ds = self.datasets[0]
          else:
               if dataset_id not in self._get_datasets():
                    raise ValueError("The dataset does not exist")
               
               ds = self.get_dataset(dataset_id)
          
          new_obs = {"node":node_id, "network":network_id, "entries":[]}

          if variable_name is not None:
               new_obs["constantName"] = variable_name
               new_obs["entries"].append({"weight":1, "value":value})
          else:
               if isinstance(value, list) and len(value)>1:
                    for vl in value:
                         new_obs["entries"].append({"weight":vl[0], "value":vl[1]})
               else:
                    new_obs["entries"].append({"weight":1, "value":value})

          if ds.observations is None:
               ds.observations = []
          
          if len(ds.observations)>0:
               obs_rewrite = False
               if variable_name is not None:     
                    for idx, obs in enumerate(ds.observations):
                         if (obs["node"] == node_id) & (obs["network"] == network_id):
                              obs_rewrite = True
                              rewrite_idx = idx
               if obs_rewrite:
                    ds.observations[rewrite_idx] = new_obs
               if not obs_rewrite:
                    ds.observations.append(new_obs)

          else:
               ds.observations.append(new_obs)
                    
     def remove_observation(self, network_id, node_id, dataset_id=None):
          if dataset_id is None:
               ds = self.datasets[0]
          else:
               if dataset_id not in self._get_datasets():
                    raise ValueError("The dataset does not exist")
               
               ds = self.get_dataset(dataset_id)

          obs_del = [obs for obs in ds.observations if obs["node"]==node_id and obs["network"]==network_id].pop()
          ds.observations.remove(obs_del)
          print("The dataset is successfully removed")

     def clear_dataset_observations(self, dataset_id):
          if dataset_id not in self._get_datasets():
               raise ValueError("The dataset does not exist")

          ds = self.get_dataset(dataset_id)     

          ds.observations = None
          print("All observations in the dataset are successfully cleared")

     def clear_all_observations(self):
          for ds in self.datasets:
               ds.observations = None
          
          print("All observations from the all datasets in the model are successfully cleared")

     def change_settings(self, **kwargs):
          for fld in kwargs:
               if fld in self.settings.keys():
                    self.settings[fld] = kwargs[fld]
                    print(f"Model setting {fld} is successfully updated")

     def default_settings(self):
          self.settings = {"parameterLearningLogging":False, "discreteTails":False, "sampleSizeRanked":5, "convergence":0.01, "simulationLogging":False, "iterations":50, "tolerance":1}
          print("Model settings are successfully reset to default")

     def save_to_file(self, filename):
          if os.path.splitext(filename)[1] == ".cmpx" or os.path.splitext(filename)[1] == ".json":
               exported = self._generate_cmpx()

               with open(filename, "w") as outfile:
                    json.dump(exported, outfile)
          else:
               raise ValueError("The input filename must have a .cmpx or .json file extension")

     def _generate_cmpx(self):
          json_settings = self.settings
          json_datasets = []
          for ds in self.datasets:
               this_ds = {}
               this_ds["id"] = ds.id
               this_ds["observations"] = ds.observations
               this_ds["results"] = ds.results
               json_datasets.append(this_ds)

          json_network_links = self.network_links

          json_networks = []
          for nt in self.networks:
               this_nt = {}
               this_nt["id"] = nt.id
               this_nt["name"] = nt.name
               this_nt["description"] = nt.description
               this_nt["nodes"] = []
               this_nt["links"] = []
               
               for nd in nt.nodes:
                    this_nd = {}
                    this_nd["id"] = nd.id
                    this_nd["name"] = nd.name
                    this_nd["description"] = nd.description
                    this_nd["configuration"] = {}
                    if nd.simulated:    this_nd["configuration"]["simulated"] = True
                    this_nd["configuration"]["type"] = nd.type
                    if nd.states is not None:   this_nd["configuration"]["states"] = nd.states
                    this_nd["configuration"]["table"] = {}
                    this_nd["configuration"]["table"]["type"] = nd.distr_type
                    if nd.probabilities is not None:    this_nd["configuration"]["table"]["probabilities"] = list(map(list, zip(*nd.probabilities)))
                    if nd.expressions is not None:  this_nd["configuration"]["table"]["expressions"] = nd.expressions
                    if nd.distr_type == "Partitioned" and nd.partitions is not None:   this_nd["configuration"]["table"]["partitions"] = nd.partitions
                    
                    if len(nd.variables)>0:
                         this_variables = nd.variables
                         this_nd["configuration"]["variables"] = []
                         for vr in this_variables:
                              this_nd["configuration"]["variables"].append({"name":[*vr].pop(),"value":[*vr.values()].pop()})
                    
                    this_nt["nodes"].append(this_nd)

                    this_parents = nd.parents
                    for pr in this_parents:
                         this_nt["links"].append({"parent":pr.id,"child":nd.id})
        
               json_networks.append(this_nt)

          json_model = {"model":{"settings":json_settings, "dataSets":json_datasets, "links": json_network_links, "networks": json_networks}}
          return json.loads(json.dumps(json_model))

     def create_batch_cases(self, data, update_model=True):
          data = pd.read_csv(data, index_col="Case")

          for ix, row in data.iterrows():
               ds_id = ix
               self.create_dataset(ix, from_cmpx=True)
               for idx, cl in enumerate(data.columns):
                    this_net = cl.split(".")[0]
                    this_node = cl.split(".")[1]
                    if not pd.isna(row[idx]):     self.enter_observation(network_id=this_net, node_id=this_node, dataset_id=ds_id, value=row[idx])
          
          if update_model:
               print("The model is sucessfully updated with new cases and observations from the dataset")
          else:
               filename = self.id+"_batch_cases"
               self.to_json(filename)
               for ix, row in data.iterrows():
                    self.remove_dataset(ix, from_cmpx=True)
               print("The model with new cases and observations is successfully exported as json, the model object does not keep new cases")

     def create_csv_template(self):
          headers = [(nt.id+"."+nd.id) for nt in self.networks for nd in nt.nodes]
          rows = [ds.id for ds in self.datasets]
          test = pd.DataFrame(columns=headers, index=rows)
          test.index.name = "Case"
          filename = self.id+"_Data.csv"
          test.to_csv(filename)

     def _import_results(self, file_path):
          with open(file_path, "r") as file:
               results_string = file.read()
          all_results = json.loads(results_string)
          for res in all_results:
               results = res["results"]
               dataset_id = res["id"]
               dataset = self.get_dataset(dataset_id)
               dataset.results = results
               dataset._convert_to_dotdict()
               print(f"Results are successfully imported to case {dataset.id}")

     def get_results(self, filename=None):

          df = pd.DataFrame(columns=["Case", "Network", "Node", "State", "Probability"])

          for ds in self.datasets:
               for rs in ds.results:
                    for rv in rs["resultValues"]:
                         df.loc[len(df)] = [ds.id, rs["network"], rs["node"], rv["label"], rv["value"]]

          if filename is not None:
               df.to_csv(filename + ".csv")
          else:
               df.to_csv(self.id + "_results.csv")

     def create_sensitivity_config(self, **kwargs):
          sens_config = {}
          for fld in kwargs:
               sens_config[fld] = kwargs[fld]
          return sens_config

     def _ds_to_json(self, dataset_ids = None):
          json_dataset = []
          if dataset_ids is None:
               for ds in self.datasets:
                    this_ds = {}
                    this_ds["id"] = ds.id
                    this_ds["observations"] = ds.observations
                    this_ds["results"] = ds.results
                    json_dataset.append(this_ds)
          else:
               for dsid in dataset_ids:
                    ds = self.get_dataset(dsid)
                    this_ds = {}
                    this_ds["id"] = ds.id
                    this_ds["observations"] = ds.observations
                    this_ds["results"] = ds.results
                    json_dataset.append(this_ds)
          
          return json_dataset

     @classmethod
     def from_cmpx(cls, filename):
          
          with open(filename, "r") as file:
               model_string = file.read()

          agena_model = json.loads(model_string)["model"]
          agena_settings = agena_model["settings"]
          agena_networks = agena_model["networks"]
          agena_datasets = agena_model["dataSets"]
          agena_network_links = agena_model["links"]
          
          agena_nodes = []
          for index, anw in enumerate(agena_networks):
               agena_nodes.append([])
               for an in anw["nodes"]:
                    agena_nodes[index].append(an)

          agena_node_links = []
          for index, anw in enumerate(agena_networks):
               agena_node_links.append([])
               for al in anw["links"]:
                    agena_node_links[index].append([al["child"], al["parent"]])

          nodes_list = []
          # creating a list of nodes with id, name, description, and type
          for idx, ntw in enumerate(agena_nodes):
               nodes_list.append([])
               for nd in ntw:
                    if "simulated" not in nd["configuration"].keys():
                         this_node = Node(id=nd["id"], name=nd["name"], type=nd["configuration"]["type"], simulated=False)
                    else:
                         this_node = Node(id=nd["id"], name=nd["name"], type=nd["configuration"]["type"], simulated=True)
                    nodes_list[idx].append(this_node)

          # adding parents to all nodes before defining distr_type, states, probabilities, expressions, and partitions
          for idx, ntw in enumerate(nodes_list):
               for nd in ntw:
                    for link in agena_node_links[idx]:
                         if nd.id == link[0]:
                              nd._addparentbyID(ntw,link[1])

          # setting distr_type, states, probabilities, expressions, and partitions for all nodes
          for idx, ntw in enumerate(agena_nodes):
               for ix, nd in enumerate(ntw):
                    this_node = nodes_list[idx][ix]
                    this_node.set_distr_type(nd["configuration"]["table"]["type"], from_cmpx=True)

                    if this_node.distr_type == "Manual":
                         this_node.states = nd["configuration"]["states"]
                         this_node.set_probabilities(nd["configuration"]["table"]["probabilities"], by_row=True)
                    if this_node.distr_type == "Expression":
                         this_node.set_expressions(nd["configuration"]["table"]["expressions"], from_cmpx=True)
                    if this_node.distr_type == "Partitioned":
                         this_node.set_expressions(nd["configuration"]["table"]["expressions"], partitioned_parents= nd["configuration"]["table"]["partitions"], from_cmpx=True)

                    if "variables" in nd["configuration"].keys():
                         for vr in nd["configuration"]["variables"]:
                              this_node.set_variable(vr["name"], vr["value"], from_cmpx=True)
          
          # creating a list of networks
          networks_list = []
          for idx, ntw in enumerate(agena_networks):
               this_net = Network(id=ntw["id"], nodes=nodes_list[idx])
               networks_list.append(this_net)

          datasets_list = []
          if len(agena_datasets)>0:
               for ds in agena_datasets:
                    this_ds = Dataset(id=ds["id"], observations=ds["observations"], results=ds["results"])
                    datasets_list.append(this_ds)


          return cls(networks=networks_list, id=None, datasets=datasets_list, network_links=agena_network_links, settings=agena_settings)