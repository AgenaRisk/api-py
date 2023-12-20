import unittest;
import pyagena;
import tests.credentials as credentials

class TestLocalActivation(unittest.TestCase):
    def test_local_activation(self):
        pyagena.local_api_activate_license(credentials.agena_key)
        mode=pyagena.local_api_get_license_summary()['Mode']
        invalid = mode in ['', 'FreeTrial', 'TimedTrial']
        self.assertFalse(invalid)

        pyagena.local_api_activate_license(credentials.agena_key)
        mode=pyagena.local_api_get_license_summary()['Mode']
        invalid = mode in ['', 'FreeTrial', 'TimedTrial']
        self.assertFalse(invalid)

        pyagena.local_api_deactivate_license()
        mode=pyagena.local_api_get_license_summary()['Mode']
        invalid = mode in ['', 'FreeTrial', 'TimedTrial']
        self.assertTrue(invalid)
        
        pyagena.local_api_deactivate_license()
        mode=pyagena.local_api_get_license_summary()['Mode']
        invalid = mode in ['', 'FreeTrial', 'TimedTrial']
        self.assertTrue(invalid)

        pyagena.local_api_activate_license(credentials.agena_key)
        mode=pyagena.local_api_get_license_summary()['Mode']
        invalid = mode in ['', 'FreeTrial', 'TimedTrial']
        self.assertFalse(invalid)

    