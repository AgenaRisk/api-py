import unittest;
import pyagena;

class TestCreateAsia(unittest.TestCase):
    def test_create_asia(self):
        model = pyagena.Model()
        model.change_settings(convergence=0.001)

        net = model.create_network(id = 'Car Costs_0', name = 'Car Costs', description = '.Car Cost Estimation')

        nCarType = net.create_node(id='car_type', name='Car type',type='Ranked')
        nCarType.set_distr_type('Manual')
        nCarType.states = ['Small', 'Medium', 'Large']

        nReliability = net.create_node(id='Reliability', name='Reliability',type='Ranked', states=['High', 'Medium', 'Low'])
        nReliability.set_distr_type('Manual')

        nMaintainability = net.create_node(id='Maintainability', name='Maintainability',type='Ranked')
        nMaintainability.set_variable('miles_per_year_const', 10000.0)
        nMaintainability.set_distr_type('Expression')
        nMaintainability.set_expressions(['TNormal(wmean(2.0,car_type,1.0,Reliability), 0.01, 0, 1)'])
        nMaintainability.add_parent(nCarType)
        nMaintainability.add_parent(nReliability)

        nAnnualMaintenanceCost = net.create_node(id='maintenance_cost', name='Annual maintenance cost ($)',type='ContinuousInterval', simulated=True)
        nAnnualMaintenanceCost.add_parent(nMaintainability)
        nAnnualMaintenanceCost.set_distr_type('Partitioned')
        nAnnualMaintenanceCost.set_expressions(['TNormal(100, 100, 0, 600)', 'TNormal(200.0,150.0,0.0,600.0)', 'TNormal(500.0,150.0,0.0,600.0)'], [nMaintainability.id])

        nMilesPerGallon = net.create_node(id='miles_per_gallon', name='Miles per gallon',type='ContinuousInterval', simulated=True)
        nMilesPerGallon.add_parent(nCarType)
        nMilesPerGallon.set_distr_type('Partitioned')
        nMilesPerGallon.set_expressions(['TNormal(35.0,50.0,5.0,100.0)', 'TNormal(28.0,50.0,5.0,100.0)', 'TNormal(18.0,30.0,5.0,100.0)'], [nCarType.id])

        nFuelPrice = net.create_node(id='Fuel_price', name='Fuel price $ (gallon)',type='ContinuousInterval', simulated=True)
        nFuelPrice.set_variable('fuel_price_const', 3)
        nFuelPrice.set_distr_type('Expression')
        nFuelPrice.set_expressions(['Arithmetic(fuel_price_const)'])

        nPricePerMile = net.create_node(id='price_per_mile', name='Price per mile $',type='ContinuousInterval', simulated=True)
        nPricePerMile.add_parent(nFuelPrice)
        nPricePerMile.add_parent(nMilesPerGallon)
        nPricePerMile.set_distr_type('Expression')
        nPricePerMile.set_expressions(['Arithmetic(Fuel_price/miles_per_gallon)'])

        nMilesPerYear = net.create_node(id='Miles_per_year', name='Miles per year',type='ContinuousInterval', simulated=True)
        nMilesPerYear.set_variable('miles_per_year_const', 10000.0)
        nMilesPerYear.set_distr_type('Expression')
        nMilesPerYear.set_expressions(['Arithmetic(miles_per_year_const)'])

        nAnnualFuelCost = net.create_node(id='total_fuel_cost', name='Annual fuel cost $',type='ContinuousInterval', simulated=True)
        nAnnualFuelCost.add_parent(nMilesPerYear)
        nAnnualFuelCost.add_parent(nPricePerMile)
        nAnnualFuelCost.set_distr_type('Expression')
        nAnnualFuelCost.set_expressions(['Arithmetic(price_per_mile*Miles_per_year)'])

        nTotalAnnualCost = net.create_node(id='total_cost', name='Total annual cost $',type='ContinuousInterval', simulated=True)
        nTotalAnnualCost.add_parent(nAnnualFuelCost)
        nTotalAnnualCost.add_parent(nAnnualMaintenanceCost)
        nTotalAnnualCost.set_distr_type('Expression')
        nTotalAnnualCost.set_expressions(['Arithmetic(maintenance_cost+total_fuel_cost)'])

        ds = model.get_dataset(dataset_index=0)

        pyagena.local_api_calculate(model, [ds.id])
        result = ds.get_result(net.id, nTotalAnnualCost.id)
        self.assertAlmostEqual(result.summaryStatistics.mean, 1562.0, delta=10)
        
        ds.enter_observation(net.id, nCarType.id, 'Medium')
        ds.enter_observation(net.id, nReliability.id, 'Low')
        ds.enter_observation(net.id, nFuelPrice.id, value=3, variable_name='fuel_price_const')
        ds.enter_observation(net.id, nMilesPerYear.id, value=7000, variable_name='miles_per_year_const')
        pyagena.local_api_calculate(model, [ds.id])
        result = ds.get_result(net.id, nTotalAnnualCost.id)
        self.assertAlmostEqual(result.summaryStatistics.mean, 1118.5, delta=10)
