import os;
import unittest;
import pyagena;

class Test2VarObservations(unittest.TestCase):
    def test_2_var_observations(self):
        model = pyagena.Model.from_cmpx(os.path.join("tests", "resources", "2obs.json"))
        ds = model.get_dataset(dataset_index=0)
        net = model.get_network(network_index=0)
        node = net.get_node(node_index=0)

        self.assertEqual(len(ds.observations), 2)
        self.assertEqual(len(ds.results), 1)

        ds.enter_observation(network_id=net.id, node_id=node.id, value=10, variable_name="a")
        ds.enter_observation(network_id=net.id, node_id=node.id, value=20, variable_name="b")

        pyagena.local_api_calculate(model, [ds.id])

        self.assertEqual(len(ds.observations), 2)
        self.assertEqual(len(ds.results), 1)

        self.assertEqual(ds.get_result(net.id, node.id).summaryStatistics.mean, 30)
        
        ds.clear_all_observations()
        self.assertEqual(len(ds.observations), 0)
        pyagena.local_api_calculate(model, [ds.id])

        self.assertEqual(ds.get_result(net.id, node.id).summaryStatistics.mean, 3)
