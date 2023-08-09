
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
