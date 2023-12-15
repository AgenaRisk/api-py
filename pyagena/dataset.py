import logging

class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
    
class Dataset():
    def __init__(self, id, observations = None, results=None):
         
        self.id = str(id)
        if observations is not None:
            self.observations = observations
        else:
            self.observations = []
        
        if results is not None:
            self.results = results
        else:
            self.results = []
        
        self._convert_to_dotdict()
    
    def get_result(self, network_id, node_id, node_state = None):
            result = [res for res in self.results if res.node == node_id and res.network == network_id]
            if len(result) == 0:
                return None
            else:
                result = result.pop()
                if node_state is not None:
                    all_states = [st["label"] for st in result["resultValues"]]
                    if node_state not in all_states:
                        raise ValueError(f"The result does not have a value for the state {node_state}")
                    else:
                        state_value = [rv for rv in result['resultValues'] if rv['label'] == node_state].pop()['value']
                    return state_value
                else:
                    return result

        
    def enter_observation(self, network_id, node_id, value, variable_name=None):
          
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

        if self.observations is None:
            self.observations = []
          
        if len(self.observations)>0:
            obs_rewrite = False
            var_obs_check = False

            if variable_name is None:     
                for idx, obs in enumerate(self.observations):
                    if (obs["node"] == node_id) & (obs["network"] == network_id):
                        if "constantName" not in obs.keys():
                            obs_rewrite = True
                            rewrite_idx = idx
                        else:
                            obs_rewrite = False
                            var_obs_check = True
            else:
                for idx, obs in enumerate(self.observations):
                    if (obs["node"] == node_id) & (obs["network"] == network_id):
                        if "constantName" not in obs.keys():
                            obs_rewrite = False
                        else:
                            if obs["constantName"] == variable_name:
                                obs_rewrite = True
                                rewrite_idx = idx

            if obs_rewrite:
                self.observations[rewrite_idx] = new_obs
                if variable_name is None:
                    logging.info(f"The observation of {value} is entered to the node {node_id}")
                else:
                    logging.info(f"The observation of {variable_name} = {value} is entered to the node {node_id}")
            if not obs_rewrite:
                self.observations.append(new_obs)
                if var_obs_check:
                    logging.warning(f"The observation of {value} is entered to the node {node_id} with existing variable observations, in calculations the variable observations will be ignored")
                else:
                    if variable_name is None:
                        logging.info(f"The observation of {value} is entered to the node {node_id}")
                    else:
                        logging.info(f"The observation of {variable_name} = {value} is entered to the node {node_id}")

        else:
            self.observations.append(new_obs)
            if variable_name is None:
                logging.info(f"The observation of {value} is entered to the node {node_id}")
            else:
                logging.info(f"The observation of {variable_name} = {value} is entered to the node {node_id}")

    def remove_observation(self, network_id, node_id):

        obs_del = [obs for obs in self.observations if obs["node"]==node_id and obs["network"]==network_id].pop()
        self.observations.remove(obs_del)
        logging.info("The observation is successfully removed")
    
    def clear_all_observations(self):
          self.observations = []
          logging.info("All observations in the dataset are successfully cleared")

    def _convert_to_dotdict(self):
        dot_obs = []

        for ix, ob in enumerate(self.observations):
            dot_obs.append(dotdict(ob))
            for idx, ent in enumerate(ob["entries"]):
                dot_obs[ix].entries[idx] = dotdict(ent)
        
        self.observations = dot_obs

        dot_res = []

        for ix, res in enumerate(self.results):
            dot_res.append(dotdict(res))
            if "summaryStatistics" in dot_res[ix].keys():
                dot_res[ix].summaryStatistics = dotdict(res["summaryStatistics"])
            for dx, rv in enumerate(res["resultValues"]):
                dot_res[ix].resultValues[dx] = dotdict(rv)
        
        self.results = dot_res

    def __str__(self) -> str:
        if self.results is not None:
            if self.observations is not None:
                return  "Dataset id: % s\nNumber of observations: % d\nDataset contains calculation results" % (self.id, len(self.observations))
            else:
                return "Dataset id: % s\nNumber of observations: 0\nDataset contains calculation results" % (self.id)
        else:
            if self.observations is not None:
                return  "Network id: % s\nNumber of observations: % d\nDataset does not contain calculation results" % (self.id, len(self.observations))   
            else:
                return "Dataset id: % s\nNumber of observations: 0\nDataset does not contain calculation results" % (self.id)

    def __repr__(self) -> str:
        if self.observations is not None:
            return "Dataset: % s (with % d observations)" % (self.id, len(self.observations)) 
        else:
            return "Dataset: % s (with 0 observations)" % (self.id) 

    def _to_json(self):
        json_dataset = []
        this_ds = {}
        this_ds["id"] = self.id
        this_ds["observations"] = self.observations
        this_ds["results"] = self.results
        json_dataset.append(this_ds)
        return json_dataset

    