import os;
import unittest;
import pyagena;

class TemplateLoadAsia(unittest.TestCase):
    def setUp(self):
        
        self.model = pyagena.Model.from_cmpx(os.path.join("tests", "resources", "asia.json"))
        self.ds = self.model.get_dataset(dataset_index=0)
        self.network = self.model.get_network(network_index=0)
        self.node = self.network.get_node('T')
    