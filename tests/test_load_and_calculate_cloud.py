from tests.template_load_cars import TemplateLoadCars
import unittest
import pyagena
import tests.credentials as credentials

class TestLoadAndCalculateCloud(TemplateLoadCars):

    def __init__(self, methodName: str = ...) -> None:
        super().__init__(methodName)
        self.cloudUser = pyagena.login(credentials.username, credentials.password)
        self.cloudUser.set_server_url('https://api.staging.agena.ai')

    def test_calculate_short(self):
        resultInitialFile = self.ds.get_result(self.network.id, self.nodeTotalAnnualCost.id).summaryStatistics.mean
        self.cloudUser.calculate(self.model, self.ds.id)
        resultInitialCloud = self.ds.get_result(self.network.id, self.nodeTotalAnnualCost.id).summaryStatistics.mean
        self.assertAlmostEqual(resultInitialCloud, 2290, delta=0.1)
        self.assertAlmostEqual(resultInitialCloud, resultInitialFile, delta=10)

        self.ds.enter_observation(network_id=self.network.id, node_id=self.nodeCarType.id, value="Small")
        self.ds.enter_observation(network_id=self.network.id, node_id=self.nodeMilesPerYear.id, value=1000)
        self.ds.enter_observation(network_id=self.network.id, node_id=self.nodeReliability.id, value="Low")
        self.cloudUser.calculate(self.model, self.ds.id)
        resultCustom = self.ds.get_result(self.network.id, self.nodeTotalAnnualCost.id).summaryStatistics.mean
        self.assertAlmostEqual(resultCustom, 261, delta=10)

        self.model.create_dataset('empty')
        dsEmpty = self.model.get_dataset('empty')
        self.cloudUser.calculate(self.model, dsEmpty.id)
        resultEmptyDs = dsEmpty.get_result(self.network.id, self.nodeTotalAnnualCost.id).summaryStatistics.mean
        self.assertAlmostEqual(resultEmptyDs, 1562, delta=10)

    def test_calculate_long(self):
        self.model.change_settings(convergence=0.00001)
        self.cloudUser.calculate(self.model, self.ds.id)
        result = self.ds.get_result(self.network.id, self.nodeTotalAnnualCost.id).summaryStatistics.mean
        self.assertAlmostEqual(result, 2269, delta=10)

