import tempfile;
import os;
import unittest;
import pyagena;

class TestNonStringIds(unittest.TestCase):
    def test_non_string_ids(self):
        model = pyagena.Model()
        idn1=123
        idn2=321
        model.create_network(idn1)
        model.get_network().create_node(idn2)

        tempdir = tempfile.TemporaryDirectory()
        outpath = os.path.join(tempdir.name, "test_non_string_ids.cmpx")
        model.save_to_file(outpath)

        model = pyagena.Model.from_cmpx(outpath)

        self.assertEqual(model.get_network(str(idn1)).get_node(str(idn2)).id, str(idn2))

        tempdir.cleanup()
