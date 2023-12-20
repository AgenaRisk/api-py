import os;
import tempfile;
import json
import unittest
import pyagena
import tests.credentials as credentials
from tests.template_load_cars import TemplateLoadCars

class TestBatch(TemplateLoadCars):
    def __init__(self, methodName: str = ...) -> None:
        super().__init__(methodName)
        pyagena.local_api_activate_license(credentials.agena_key)

    def setUp(self):
        super().setUp()
        self.tempdir = tempfile.TemporaryDirectory()

    def test_batch(self):
        self.model.datasets = []
        self.model.import_data(os.path.join("tests", "resources", "batch_data.csv"))

        cache_file=os.path.join(self.tempdir.name, "batch_cache_dyn.json")

        pyagena.local_api_calculate(self.model, cache_path=cache_file)

        with open(cache_file) as file:
            json_cache = json.loads(file.read())
        
        self.assertEqual(len(json_cache), 100)

        file_export_inputs_json=os.path.join(self.tempdir.name, "batch_export_inputs.json")
        self.model.export_data(filename=file_export_inputs_json, include_inputs=True, include_outputs=False)
        with open(file_export_inputs_json) as file:
            jFile = json.loads(file.read())
            self.assertEqual(len(jFile), 100)
            for ds in jFile:
                self.assertTrue('id' in ds)
                self.assertTrue(len(ds['observations']) > 0)
                self.assertTrue('results' not in ds or len(ds['results']) == 0)

        file_export_outputs_json=os.path.join(self.tempdir.name, "batch_export_outputs.json")
        self.model.export_data(filename=file_export_outputs_json, include_inputs=False, include_outputs=True)
        with open(file_export_outputs_json) as file:
            jFile = json.loads(file.read())
            self.assertEqual(len(jFile), 100)
            for ds in jFile:
                self.assertTrue('id' in ds)
                self.assertTrue(len(ds['results']) > 0)
                self.assertTrue('observations' not in ds or len(ds['observations']) == 0)

        file_export_full_json=os.path.join(self.tempdir.name, "batch_export_full.json")
        self.model.export_data(filename=file_export_full_json, include_inputs=True, include_outputs=True)
        with open(file_export_full_json) as file:
            jFile = json.loads(file.read())
            self.assertEqual(len(jFile), 100)
            for ds in jFile:
                self.assertTrue('id' in ds)
                self.assertTrue(len(ds['results']) > 0)
                self.assertTrue(len(ds['observations']) > 0)


        file_export_inputs_csv=os.path.join(self.tempdir.name, "batch_export_inputs.csv")
        self.model.export_data(filename=file_export_inputs_csv, include_inputs=True, include_outputs=False)
        with open(file_export_inputs_csv) as file:
            line_count=0
            for line in file:
                if not line.isspace():
                    line_count+=1
            self.assertEqual(line_count, 349)

        file_export_outputs_csv=os.path.join(self.tempdir.name, "batch_export_outputs.csv")
        self.model.export_data(filename=file_export_outputs_csv, include_inputs=False, include_outputs=True)
        with open(file_export_outputs_csv) as file:
            line_count=0
            for line in file:
                if not line.isspace():
                    line_count+=1
                if line_count > 10000:
                    break
            self.assertTrue(line_count > 10000)
        
        file_export_outputs_csv_excel=os.path.join(self.tempdir.name, "batch_export_outputs_excel.csv")
        self.model.export_data(filename=file_export_outputs_csv_excel, include_inputs=False, include_outputs=True, excel_compatibility=True)
        with open(file_export_outputs_csv_excel) as file:
            file.readline() # Skip header line
            line=file.readline().strip('\n')
            cell_state=line.split(',')[3]
            self.assertTrue(cell_state.startswith("\"=\"\"") and cell_state.endswith("\"\"\""))

        self.model.datasets=[]
        self.assertEqual(len(self.model.datasets), 0)
        self.model.import_data(file_export_full_json)
        self.assertEqual(len(self.model.datasets), 100)

        file_full_batch_model=os.path.join(self.tempdir.name, "batch_imported_from_json.cmpx")
        self.model.save_to_file(file_full_batch_model)
        model2 = pyagena.Model.from_cmpx(file_full_batch_model)
        self.assertEqual(len(model2.datasets), 100)

    def tearDown(self):
        self.tempdir.cleanup()
