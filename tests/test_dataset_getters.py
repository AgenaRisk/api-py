from tests.template_load_asia import TemplateLoadAsia
from tests.template_load_cars import TemplateLoadCars
import unittest

class TestDatasetGetters1(TemplateLoadAsia):
    def test_get_valid_state_result(self):
        self.assertAlmostEqual(self.ds.get_result(self.network.id, self.node.id, 'yes'), 0.01039, delta=0.05)

    def test_get_invalid_state_result(self):
        with self.assertRaises(ValueError):
            self.ds.get_result(self.network.id, self.node.id, 'foobar')

    def test_get_nonexistent_result(self):
        self.assertEqual(self.ds.get_result('foo', 'bar'), None)
        self.assertEqual(self.ds.get_result(self.network.id, 'bar'), None)
        self.assertEqual(self.ds.get_result('foo', self.node.id), None)

class TestDatasetGetters2(TemplateLoadCars):
    def test_get_summary_stat(self):
        self.assertAlmostEqual(self.ds.get_result(self.network.id, self.nodeTotalAnnualCost.id).summaryStatistics.mean, 2298, delta=50)
