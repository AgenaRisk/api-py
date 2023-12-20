import unittest;
import pyagena;

class TestCreateAsia(unittest.TestCase):
    def test_create_asia(self):
        model = pyagena.Model()
        model.change_settings(convergence=0.01)

        net = model.create_network(id = 'Asia?_0', name = 'Asia?', description = '.Asia?')

        nVisitAsia = net.create_node(id='A', name='Visit to Asia?',type='Labelled', states=['yes', 'no'])
        nVisitAsia.set_probabilities([[
            0.01,
            0.99
        ]])

        nHasTuberculosis = net.create_node(id='T', name='Has tuberculosis',type='Labelled', states=['yes', 'no'])
        nHasTuberculosis.add_parent(nVisitAsia)
        nHasTuberculosis.set_probabilities([
            [0.05, 0.01],
            [0.95, 0.99]
        ], True)

        nSmoker = net.create_node(id='S', name='Smoker?',type='Labelled', states=['yes', 'no'])

        nHasLungCancer = net.create_node(id='L', name='Has lung cancer',type='Labelled', states=['yes', 'no'])
        nHasLungCancer.add_parent(nSmoker)
        nHasLungCancer.set_probabilities([
            [0.1, 0.01],
            [0.9, 0.99]
        ], True)
        
        nTuberculosisOrCancer = net.create_node(id='TBoC', name='Tuberculosis or cancer',type='Labelled', states=['yes', 'no'])
        nTuberculosisOrCancer.add_parent(nHasTuberculosis)
        nTuberculosisOrCancer.add_parent(nHasLungCancer)
        nTuberculosisOrCancer.set_probabilities([
            [1.0, 1.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ], True)

        nHasBronchitis = net.create_node(id='B', name='Has bronchitis',type='Labelled', states=['yes', 'no'])
        nHasBronchitis.add_parent(nSmoker)
        nHasBronchitis.set_probabilities([
            [0.6, 0.3],
            [0.4, 0.7]
        ], True)

        nPositiveXray = net.create_node(id='X', name='Positive X-ray?',type='Labelled', states=['yes', 'no'])
        nPositiveXray.add_parent(nTuberculosisOrCancer)
        nPositiveXray.set_probabilities([
            [0.98, 0.05],
            [0.02, 0.95]
        ], True)

        nDyspnoea = net.create_node(id='D', name='Dyspnoea?',type='Labelled', states=['yes', 'no'])
        nDyspnoea.add_parent(nHasBronchitis)
        nDyspnoea.add_parent(nTuberculosisOrCancer)
        nDyspnoea.set_probabilities([
            [0.9, 0.8, 0.7, 0.1],
            [0.1, 0.2, 0.3, 0.9]
        ], True)

        ds = model.get_dataset(dataset_index=0)

        pyagena.local_api_calculate(model, [ds.id])
        result = ds.get_result(net.id, nDyspnoea.id, 'yes')
        self.assertAlmostEqual(result, 0.43597, delta=0.01)
        
        ds.enter_observation(net.id, nHasBronchitis.id, 'yes')
        ds.enter_observation(net.id, nHasTuberculosis.id, 'yes')
        pyagena.local_api_calculate(model, [ds.id])
        result = ds.get_result(net.id, nDyspnoea.id, 'yes')
        self.assertAlmostEqual(result, 0.9, delta=0.01)
