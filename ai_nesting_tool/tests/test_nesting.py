import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.dxf_parser import parse_dxf
from src.nesting_optimizer import NestingOptimizer

# 确保 DXF 文件存在
dxf_file = "G:/VS_code/Polyboard_7.09a_To_YunXi/ai_nesting_tool/examples/parts.dxf"
if not os.path.exists(dxf_file):
    print(f"Error: DXF file not found at {dxf_file}")
    sys.exit(1)

parts = parse_dxf(dxf_file)
optimizer = NestingOptimizer(parts, 1200, 1200)
solution = optimizer.genetic_algorithm(generations=5)
print("Solution:", solution)
print("Sheets:", optimizer.sheets)