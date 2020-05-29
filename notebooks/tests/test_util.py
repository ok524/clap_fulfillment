import unittest
from vglib.vglib2 import Vglib

text = """Cheer Active yeah"""

# python3 -m unittest tests/test_vglib_gender.py
class TestMethods(unittest.TestCase):

    def test_gender_load_custom_dict(self):
        vg = Vglib()
        vg.function_add('gender', 'GenderIdentify')
        task_description = {
            "uuid": "",
            "userid": "",
            "timestamp_st": "",
            "function": "gender",
            "params": {
                "text": text,
                "lang": "eng",
                "custom_dict_path": "./gender_dict.txt"
            },
            "resources": {
                "cpu": {},
                "ram": {},
                "storage": {},
            }
        }
        worker = vg.task_dispatch(task_description)
        ret = worker.load_pipeline()
        print(ret)

    # def test_split(self):
    #     s = 'hello world'
    #     self.assertEqual(s.split(), ['hello', 'world'])
    #     # check that s.split fails when the separator is not a string
    #     with self.assertRaises(TypeError):
    #         s.split(2)

if __name__ == '__main__':
    unittest.main()
