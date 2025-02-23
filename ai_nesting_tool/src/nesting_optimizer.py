import numpy as np
import random  # 添加这一行
from shapely.geometry import Point
from shapely.affinity import translate, rotate

class NestingOptimizer:
    def __init__(self, parts_data, sheet_width, sheet_height, max_sheets=10):
        if isinstance(parts_data, tuple):
            self.parts, self.main_polylines = parts_data
        else:
            self.parts = parts_data
            self.main_polylines = None
            
        if not self.parts:
            raise ValueError("Parts list cannot be empty")
            
        self.sheet_width = sheet_width
        self.sheet_height = sheet_height
        self.max_sheets = max_sheets
        self.sheets = {}
        self.transformed_entities = {}  # 用于存储变换后的所有实体（包括子实体）

    def fitness(self, solution):
        """计算适应度，确保返回浮点数"""
        try:
            # 如果只有一个零件，处理特殊情况
            if len(self.parts) == 1:
                if not solution or len(solution) != 1:
                    return 0.0
                    
                x, y, angle, sheet_idx = solution[0]
                part = rotate(self.parts[0], angle, origin='centroid')
                part = translate(part, x, y)
                
                # 检查是否在板材内
                sheet_boundary = Point(0, 0).buffer(self.sheet_width, self.sheet_height)
                if not sheet_boundary.contains(part):
                    return 0.0
                    
                # 单个零件，计算材料利用率
                total_area = float(part.area)
                sheet_area = self.sheet_width * self.sheet_height
                return total_area / sheet_area
            
            # 多个零件的处理逻辑（原代码）
            if not solution or len(solution) != len(self.parts):
                print(f"Invalid solution in fitness: {solution}")
                return 0.0
                
            sheets_used = {}
            for i, (x, y, angle, sheet_idx) in enumerate(solution):
                part = rotate(self.parts[i], angle, origin='centroid')
                part = translate(part, x, y)
                if sheet_idx not in sheets_used:
                    sheets_used[sheet_idx] = []
                sheets_used[sheet_idx].append(part)
            
            for sheet_idx, parts in sheets_used.items():
                for i, p1 in enumerate(parts):
                    for p2 in parts[i+1:]:
                        if p1.intersects(p2):
                            return 0.0
                    if not Point(0, 0).buffer(self.sheet_width, self.sheet_height).contains(p1):
                        return 0.0
            
            total_area = float(sum(p.area for p in self.parts))
            total_sheet_area = len(sheets_used) * self.sheet_width * self.sheet_height
            if total_sheet_area == 0:
                return 0.0
            return total_area / total_sheet_area
            
        except Exception as e:
            print(f"Error in fitness: {e}")
            return 0.0

    def genetic_algorithm(self, population_size=100, generations=50):
        # 对单个零件进行优化处理
        if len(self.parts) == 1:
            print("单零件优化...")
            # 简化的单零件优化
            best_fitness = 0.0
            best_solution = None
            
            # 获取零件的边界框
            minx, miny, maxx, maxy = self.parts[0].bounds
            part_width = maxx - minx
            part_height = maxy - miny
            
            # 生成一些随机位置和角度的候选解
            attempts = 0
            max_attempts = 500  # 增加尝试次数
            
            while attempts < max_attempts:
                attempts += 1
                
                # 确保零件完全在板内
                margin_x = max(0, self.sheet_width - part_width)
                margin_y = max(0, self.sheet_height - part_height)
                
                # 如果零件太大放不进板材，使用中心位置
                x = random.uniform(0, max(1, margin_x)) if margin_x > 0 else self.sheet_width / 2
                y = random.uniform(0, max(1, margin_y)) if margin_y > 0 else self.sheet_height / 2
                
                # 使用多种角度尝试
                angles = [0, 90, 180, 270] if attempts < 100 else [random.uniform(0, 360)]
                
                for angle in angles:
                    solution = [(x, y, angle, 0)]  # 单零件总是放在第一个板上
                    fit = self.fitness(solution)
                    
                    if fit > best_fitness:
                        best_fitness = fit
                        best_solution = solution
                        print(f"找到更好的解决方案: 位置=({x:.2f}, {y:.2f}), 角度={angle}, 适应度={fit:.4f}")
                        
                        # 如果找到合理好的解决方案就提前结束
                        if fit > 0.1:  # 根据您的需求调整阈值
                            break
            
            # 如果没有找到任何有效解决方案，创建一个默认解决方案
            if best_solution is None:
                print("警告: 未找到有效解决方案，使用默认中心位置")
                # 默认放在板材中心
                default_x = self.sheet_width / 2
                default_y = self.sheet_height / 2
                best_solution = [(default_x, default_y, 0, 0)]
            
            print(f"最终解决方案: {best_solution}, 适应度: {best_fitness:.4f}")
            self.sheets = self._layout_sheets(best_solution)
            return best_solution
            
        # 多零件优化的原逻辑
        population = [[(random.uniform(0, self.sheet_width * 0.8), 
                        random.uniform(0, self.sheet_height * 0.8), 
                        random.uniform(0, 360), 
                        random.randint(0, self.max_sheets-1)) for _ in range(len(self.parts))] 
                      for _ in range(population_size)]
        
        print(f"Initial population size: {len(population)}")
        
        for gen in range(generations):
            scores = []
            for ind in population:
                fit = self.fitness(ind)
                scores.append((fit, ind))
            print(f"Generation {gen}: Sample scores = {scores[:5]}")
            if not scores:
                raise ValueError("Scores list is empty")
            scores = sorted(scores, key=lambda x: x[0], reverse=True)
            parents = [ind for _, ind in scores[:population_size//2]]
            offspring = []
            for _ in range(population_size//2):
                p1, p2 = random.sample(parents, 2)
                child = [(random.choice([p1[i][j], p2[i][j]]) + random.uniform(-1, 1) 
                          if j < 3 else random.choice([p1[i][j], p2[i][j]]) 
                          for j in range(4)) for i in range(len(self.parts))]
                if not child or len(child) != len(self.parts):
                    print(f"Invalid child generated: {child}")
                    child = p1  # 回退到父代，避免空解
                offspring.append(child)
            population = parents + offspring
            # 过滤无效解
            population = [ind for ind in population if ind and len(ind) == len(self.parts)]
            print(f"Population size after generation {gen}: {len(population)}")
        
        if not population:
            raise ValueError("Population is empty after evolution")
        print(f"Final population sample: {population[:5]}")
        best_solution = max(population, key=self.fitness)
        print(f"Best solution: {best_solution}")
        if not best_solution or len(best_solution) != len(self.parts):
            raise ValueError(f"Invalid best_solution: {best_solution}")
        self.sheets = self._layout_sheets(best_solution)
        print(f"Generated sheets: {list(self.sheets.keys())}")
        return best_solution

    def _layout_sheets(self, solution):
        # 增加安全检查
        if not solution:
            raise ValueError("Solution cannot be None or empty")
            
        if len(solution) != len(self.parts):
            raise ValueError(f"Invalid solution length: expected {len(self.parts)}, got {len(solution)}")
            
        sheets = {}
        self.transformed_entities = {}
        
        for i, (x, y, angle, sheet_idx) in enumerate(solution):
            # 变换主要部件
            part = rotate(self.parts[i], angle, origin='centroid')
            part = translate(part, x, y)
            
            if sheet_idx not in sheets:
                sheets[sheet_idx] = []
                self.transformed_entities[sheet_idx] = []
                
            sheets[sheet_idx].append(part)
            
            # 如果有子实体信息，也对它们进行变换
            if self.main_polylines:
                for main_poly in self.main_polylines:
                    if main_poly['polygon'] == self.parts[i]:
                        # 创建一个包含所有变换后实体的字典
                        transformed_entity = {
                            'main': part,
                            'children': []
                        }
                        
                        # 变换所有子实体
                        for child in main_poly['children']:
                            if child['type'] == 'circle':
                                # 变换圆心
                                old_center = Point(child['center'])
                                new_center = rotate(old_center, angle, origin='centroid')
                                new_center = translate(new_center, x, y)
                                
                                # 变换多边形表示
                                transformed_poly = rotate(child['polygon'], angle, origin='centroid')
                                transformed_poly = translate(transformed_poly, x, y)
                                
                                transformed_entity['children'].append({
                                    'type': 'circle',
                                    'center': (new_center.x, new_center.y),
                                    'radius': child['radius'],
                                    'polygon': transformed_poly
                                })
                            elif child['type'] == 'polyline':
                                # 变换多段线
                                transformed_poly = rotate(child['polygon'], angle, origin='centroid')
                                transformed_poly = translate(transformed_poly, x, y)
                                
                                transformed_entity['children'].append({
                                    'type': 'polyline',
                                    'polygon': transformed_poly
                                })
                        
                        self.transformed_entities[sheet_idx].append(transformed_entity)
                        break
        
        if not sheets:
            raise ValueError("No sheets generated from solution")
        return sheets