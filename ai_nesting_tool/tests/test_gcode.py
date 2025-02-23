import unittest
from src.dxf_parser import parse_dxf
from src.nesting_optimizer import NestingOptimizer
from src.gcode_generator import generate_gcode

class TestGcode(unittest.TestCase):
    def test_gcode(self):
        parts = parse_dxf("../examples/parts.dxf")
        optimizer = NestingOptimizer(parts, 1000, 500)
        optimizer.genetic_algorithm(population_size=10, generations=5)
        path = generate_gcode(optimizer.sheets, "test.nc")
        with open(path) as f:
            self.assertTrue("G21" in f.read())

if __name__ == "__main__":
    unittest.main()