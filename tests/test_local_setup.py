import unittest;
import pyagena;

class TestLocalSetup(unittest.TestCase):
    # @unittest.skip("Won't work on headless os")
    def test_local_setup(self):
        pyagena.local_api_init(verbose=True)
        pyagena.local_api_get_license_summary()


    