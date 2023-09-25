class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
    
class Dataset():
    def __init__(self, id, observations = None, results=None):
         
        self.id = id
        if observations is not None:
            self.observations = observations
        else:
            self.observations = []
        
        if results is not None:
            self.results = results
        else:
            self.results = []
        
        self._convert_to_dotdict()
    
    def get_result(self, network_id, node_id):
        result = [res for res in self.results if res.node == node_id and res.network == network_id]
        if len(result) == 1:
            return result.pop()
        if len(result) == 0:
            return None
        
    def enter_observation_to_dataset(self):
        pass

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

    