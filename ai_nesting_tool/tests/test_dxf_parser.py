import unittest
from src.dxf_parser import parse_dxf

class TestDxfParser(unittest.TestCase):
    def test_parse_dxf(self):
        parts = parse_dxf("../examples/parts.dxf")
        self.assertTrue(len(parts) > 0)

if __name__ == "__main__":
    unittest.main()