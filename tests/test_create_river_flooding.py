import unittest;
import pyagena;

class TestCreateRiverFlooding(unittest.TestCase):
    
    def test_create_river_flooding(self):
        model = pyagena.Model()
        model.change_settings(convergence=0.01)

        ### NET_1 ###
        net_1 = model.create_network(id = 'net_1')

        nodeRain_1 = net_1.create_node(id='nodeRain_1', type='Ranked')
        nodeRain_1.states=['None', 'Low Rainfall', 'High Rainfall']
        nodeRain_1.set_probabilities([[
            0.16666667,
            0.33333334,
            0.5
        ]])

        nodePriorWaterLevel_1 = net_1.create_node(id='nodePriorWaterLevel_1', type='Ranked')
        nodePriorWaterLevel_1.set_states(['Low', 'Medium', 'High'])
        nodePriorWaterLevel_1.set_probabilities([[
            0.5,
            0.33333334,
            0.16666667
        ]])

        nodePostWaterLevel_1 = net_1.create_node(id='nodePostWaterLevel_1', type='Ranked')
        nodePostWaterLevel_1.set_states(['Low', 'Medium', 'High'])
        nodePostWaterLevel_1.add_parent(nodePriorWaterLevel_1)
        nodePostWaterLevel_1.add_parent(nodeRain_1)
        nodePostWaterLevel_1.set_probabilities([
            [1.0, 0.9, 0.2, 0.7, 0.1, 0.0, 0.1, 0.0, 0.0],
            [0.0, 0.1, 0.7, 0.3, 0.8, 0.2, 0.7, 0.1, 0.0],
            [0.0, 0.0, 0.1, 0.0, 0.1, 0.8, 0.2, 0.9, 1.0]
        ], True)

        nodeFloodDefences_1 = net_1.create_node(id='nodeFloodDefences_1', type='Ranked')
        nodeFloodDefences_1.set_states(['Poor', 'Medium', 'High'])
        nodeFloodDefences_1.set_probabilities([[
            0.16666667,
            0.33333334,
            0.5
        ]])

        nodeFloodDefencesOutput_1 = net_1.create_node(id='nodeFloodDefencesOutput_1', type='Ranked')
        nodeFloodDefencesOutput_1.set_states(['Poor', 'Medium', 'High'])
        nodeFloodDefencesOutput_1.add_parent(nodeFloodDefences_1)
        nodeFloodDefencesOutput_1.set_probabilities([
            [1.0, 0.1, 0.0],
            [0.0, 0.9, 0.1],
            [0.0, 0.0, 0.9]
        ], True)

        nodeFlood_1 = net_1.create_node(id='nodeFlood_1', type='Ranked')
        nodeFlood_1.set_states(['No', 'Yes'])
        nodeFlood_1.add_parent(nodeFloodDefences_1)
        nodeFlood_1.add_parent(nodePostWaterLevel_1)
        nodeFlood_1.set_distr_type('Expression')
        nodeFlood_1.set_expressions(['TNormal(nodePostWaterLevel_1-nodeFloodDefences_1, 0.1, 0, 1)'])

        ### NET_2 ###
        net_2 = model.create_network(id = 'net_2')

        nodeRain_2 = net_2.create_node(id='nodeRain_2', type='Ranked')
        nodeRain_2.set_states(['None', 'Low Rainfall', 'High Rainfall'])
        nodeRain_2.set_probabilities([[
            0.16666667,
            0.33333334,
            0.5
        ]])

        nodePriorWaterLevel_2 = net_2.create_node(id='nodePriorWaterLevel_2', type='Ranked')
        nodePriorWaterLevel_2.set_states(['Low', 'Medium', 'High'])
        nodePriorWaterLevel_2.set_probabilities([[
            0.5,
            0.33333334,
            0.16666667
        ]])

        nodePostWaterLevel_2 = net_2.create_node(id='nodePostWaterLevel_2', type='Ranked')
        nodePostWaterLevel_2.set_states(['Low', 'Medium', 'High'])
        nodePostWaterLevel_2.add_parent(nodePriorWaterLevel_2)
        nodePostWaterLevel_2.add_parent(nodeRain_2)
        nodePostWaterLevel_2.set_probabilities([
            [1.0, 0.9, 0.2, 0.7, 0.1, 0.0, 0.1, 0.0, 0.0],
            [0.0, 0.1, 0.7, 0.3, 0.8, 0.2, 0.7, 0.1, 0.0],
            [0.0, 0.0, 0.1, 0.0, 0.1, 0.8, 0.2, 0.9, 1.0]
        ], True)

        nodeFloodDefences_2 = net_2.create_node(id='nodeFloodDefences_2', type='Ranked')
        nodeFloodDefences_2.set_states(['Poor', 'Medium', 'High'])
        nodeFloodDefences_2.set_probabilities([[
            0.16666667,
            0.33333334,
            0.5
        ]])

        nodeFloodDefencesOutput_2 = net_2.create_node(id='nodeFloodDefencesOutput_2', type='Ranked')
        nodeFloodDefencesOutput_2.set_states(['Poor', 'Medium', 'High'])
        nodeFloodDefencesOutput_2.add_parent(nodeFloodDefences_2)
        nodeFloodDefencesOutput_2.set_probabilities([
            [1.0, 0.1, 0.0],
            [0.0, 0.9, 0.1],
            [0.0, 0.0, 0.9]
        ], True)

        nodeFlood_2 = net_2.create_node(id='nodeFlood_2', type='Ranked')
        nodeFlood_2.set_states(['No', 'Yes'])
        nodeFlood_2.add_parent(nodeFloodDefences_2)
        nodeFlood_2.add_parent(nodePostWaterLevel_2)
        nodeFlood_2.set_distr_type('Expression')
        nodeFlood_2.set_expressions(['TNormal(nodePostWaterLevel_2-nodeFloodDefences_2, 0.1, 0, 1)'])

        ### NET_3 ###
        net_3 = model.create_network(id = 'net_3')

        nodeRain_3 = net_3.create_node(id='nodeRain_3', type='Ranked')
        nodeRain_3.set_states(['None', 'Low Rainfall', 'High Rainfall'])
        nodeRain_3.set_probabilities([[
            0.16666667,
            0.33333334,
            0.5
        ]])

        nodePriorWaterLevel_3 = net_3.create_node(id='nodePriorWaterLevel_3', type='Ranked')
        nodePriorWaterLevel_3.set_states(['Low', 'Medium', 'High'])
        nodePriorWaterLevel_3.set_probabilities([[
            0.5,
            0.33333334,
            0.16666667
        ]])

        nodePostWaterLevel_3 = net_3.create_node(id='nodePostWaterLevel_3', type='Ranked')
        nodePostWaterLevel_3.set_states(['Low', 'Medium', 'High'])
        nodePostWaterLevel_3.add_parent(nodePriorWaterLevel_3)
        nodePostWaterLevel_3.add_parent(nodeRain_3)
        nodePostWaterLevel_3.set_probabilities([
            [1.0, 0.9, 0.2, 0.7, 0.1, 0.0, 0.1, 0.0, 0.0],
            [0.0, 0.1, 0.7, 0.3, 0.8, 0.2, 0.7, 0.1, 0.0],
            [0.0, 0.0, 0.1, 0.0, 0.1, 0.8, 0.2, 0.9, 1.0]
        ], True)

        nodeFloodDefences_3 = net_3.create_node(id='nodeFloodDefences_3', type='Ranked')
        nodeFloodDefences_3.set_states(['Poor', 'Medium', 'High'])
        nodeFloodDefences_3.set_probabilities([[
            0.16666667,
            0.33333334,
            0.5
        ]])

        nodeFloodDefencesOutput_3 = net_3.create_node(id='nodeFloodDefencesOutput_3', type='Ranked')
        nodeFloodDefencesOutput_3.set_states(['Poor', 'Medium', 'High'])
        nodeFloodDefencesOutput_3.add_parent(nodeFloodDefences_3)
        nodeFloodDefencesOutput_3.set_probabilities([
            [1.0, 0.1, 0.0],
            [0.0, 0.9, 0.1],
            [0.0, 0.0, 0.9]
        ], True)

        nodeFlood_3 = net_3.create_node(id='nodeFlood_3', type='Ranked')
        nodeFlood_3.set_states(['No', 'Yes'])
        nodeFlood_3.add_parent(nodeFloodDefences_3)
        nodeFlood_3.add_parent(nodePostWaterLevel_3)
        nodeFlood_3.set_distr_type('Expression')
        nodeFlood_3.set_expressions(['TNormal(nodePostWaterLevel_3-nodeFloodDefences_3, 0.1, 0, 1)'])

        model.add_network_link(
            source_network_id=net_1.id,
            source_node_id=nodePostWaterLevel_1.id,
            target_network_id=net_2.id,
            target_node_id=nodePriorWaterLevel_2.id,
            link_type="Marginals"
        )
        model.add_network_link(
            source_network_id=net_1.id,
            source_node_id=nodeFloodDefencesOutput_1.id,
            target_network_id=net_2.id,
            target_node_id=nodeFloodDefences_2.id,
        )
        model.add_network_link(
            source_network_id=net_2.id,
            source_node_id=nodePostWaterLevel_2.id,
            target_network_id=net_3.id,
            target_node_id=nodePriorWaterLevel_3.id,
        )
        model.add_network_link(
            source_network_id=net_2.id,
            source_node_id=nodeFloodDefencesOutput_2.id,
            target_network_id=net_3.id,
            target_node_id=nodeFloodDefences_3.id,
        )

        ds = model.get_dataset(dataset_index=0)

        pyagena.local_api_calculate(model, [ds.id])
        result = ds.get_result(net_3.id, nodeFlood_3.id, 'Yes')
        self.assertAlmostEqual(result, 0.22047, delta=0.01)
        
        ds.enter_observation(net_1.id, nodeRain_1.id, 'High Rainfall')
        ds.enter_observation(net_1.id, nodeFloodDefences_1.id, 'High')
        ds.enter_observation(net_2.id, nodeRain_2.id, 'Low Rainfall')
        ds.enter_observation(net_2.id, nodeFloodDefences_2.id, 'Medium')
        ds.enter_observation(net_3.id, nodeRain_3.id, 'None')
        ds.enter_observation(net_3.id, nodeFloodDefences_3.id, 'Poor')

        pyagena.local_api_calculate(model, [ds.id], verbose=True)
        result = ds.get_result(net_3.id, nodeFlood_3.id, 'Yes')
        self.assertAlmostEqual(result, 0.27927, delta=0.01)
