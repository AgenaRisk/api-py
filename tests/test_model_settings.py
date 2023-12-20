import unittest;
import pyagena;

class TestModelSettings(unittest.TestCase):
    def test_model_settings(self):
        model = pyagena.Model()
        model.create_network("net")
        model.get_network().create_node("node")

        # print(model.settings)

        self.assertEqual(model.settings['parameterLearningLogging'], False)
        self.assertEqual(model.settings['discreteTails'], False)
        self.assertEqual(model.settings['sampleSizeRanked'], 5)
        self.assertEqual(model.settings['convergence'], 0.01)
        self.assertEqual(model.settings['simulationLogging'], False)
        self.assertEqual(model.settings['iterations'], 50)
        self.assertEqual(model.settings['tolerance'], 1)

        model.change_settings(iterations=30, convergence=0.001)
        self.assertEqual(model.settings['convergence'], 0.001)
        self.assertEqual(model.settings['iterations'], 30)

        model.change_settings(iterations=45)
        self.assertEqual(model.settings['convergence'], 0.001)
        self.assertEqual(model.settings['iterations'], 45)
        