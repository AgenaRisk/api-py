import os;
import unittest
import pyagena

class TemplateLoadCars(unittest.TestCase):
    def setUp(self):
        self.model = pyagena.Model.from_cmpx(os.path.join("tests", "resources", "car_costs.json"))
        self.ds = self.model.get_dataset('mercedes')
        self.network = self.model.get_network(network_index=0)
        self.nodeCarType = self.network.get_node('car_type')
        self.nodeMilesPerYear = self.network.get_node('Miles_per_year')
        self.nodeReliability = self.network.get_node('Reliability')
        self.nodeTotalAnnualCost = self.network.get_node('total_cost')
