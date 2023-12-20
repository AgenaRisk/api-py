from tests.template_load_cars import TemplateLoadCars
import unittest
import pyagena
import tests.credentials as credentials

class TestLoadAndCalculateLocal(TemplateLoadCars):

    def __init__(self, methodName: str = ...) -> None:
        super().__init__(methodName)
        pyagena.local_api_activate_license(credentials.agena_key)

    def test_sensitivity_local(self):
        dsMercedes = self.model.get_dataset('mercedes')
        net = self.model.get_network()
        nTotalAnnualCost = net.get_node('total_cost')

        sensConfig = self.model.create_sensitivity_config(
            network = net.id,
            targetNode = nTotalAnnualCost.id,
            sensitivityNodes = "*",
            dataSet = dsMercedes.id,
            report_settings = {"summaryStats": ["mean", "variance"]}
        )

        sensitivityReport = pyagena.local_api_sensitivity_analysis(self.model, sensConfig)

        self.assertEqual(sensitivityReport.tornadoGraphs[0].summaryStatistic, 'mean')
        self.assertAlmostEqual(sensitivityReport.tornadoGraphs[0].graphBars[0]['valueMin'], 744, delta=10)

        nCarType = net.get_node('car_type')
        nMilesPerYear = net.get_node('Miles_per_year')
        nReliability = net.get_node('Reliability')
        dsMercedes.enter_observation(network_id=net.id, node_id=nCarType.id, value="Small")
        dsMercedes.enter_observation(network_id=net.id, node_id=nMilesPerYear.id, value=1000)
        dsMercedes.enter_observation(network_id=net.id, node_id=nReliability.id, value="Low")

        sensitivityReport = pyagena.local_api_sensitivity_analysis(self.model, sensConfig)

        self.assertEqual(sensitivityReport.tornadoGraphs[0].summaryStatistic, 'mean')
        self.assertAlmostEqual(sensitivityReport.tornadoGraphs[0].graphBars[0]['valueMin'], 208, delta=10)

