import ezdxf
import math
from shapely.geometry import Polygon

def parse_dxf(file_path):
    doc = ezdxf.readfile(file_path)
    msp = doc.modelspace()
    parts = []
    
    # 步骤1: 查找主要的LWPOLYLINE (包含'110OO'的图层)
    main_polylines = []
    for entity in msp.query("LWPOLYLINE"):
        if '110OO' in entity.dxf.layer:
            points = [(p[0], p[1]) for p in entity.get_points()]
            if len(points) >= 3:  # 确保至少有3个点以形成有效多边形
                poly = Polygon(points)
                main_polylines.append({
                    'polygon': poly,
                    'entity': entity,
                    'children': []  # 将存储此多边形内的其他实体
                })
    
    # 步骤2: 为每个主多边形收集内部实体
    for entity in msp.query("CIRCLE"):
        center = (entity.dxf.center[0], entity.dxf.center[1])
        radius = entity.dxf.radius
        
        # 创建一个表示圆的多边形
        circle_points = []
        for i in range(24):
            angle = 2 * math.pi * i / 24
            x = center[0] + radius * math.cos(angle)
            y = center[1] + radius * math.sin(angle)
            circle_points.append((x, y))
        circle_poly = Polygon(circle_points)
        
        # 检查此圆是否在任何主多边形内部
        for main_poly in main_polylines:
            if main_poly['polygon'].contains(circle_poly.centroid):
                # 将圆存储为主多边形的子实体
                main_poly['children'].append({
                    'type': 'circle',
                    'center': center,
                    'radius': radius,
                    'polygon': circle_poly
                })
                break
    
    # 也收集内部的其他LWPOLYLINE
    for entity in msp.query("LWPOLYLINE"):
        if '110OO' not in entity.dxf.layer:  # 跳过主多边形
            points = [(p[0], p[1]) for p in entity.get_points()]
            if len(points) >= 3:
                inner_poly = Polygon(points)
                
                # 检查这个多段线是否在任何主多边形内部
                for main_poly in main_polylines:
                    if main_poly['polygon'].contains(inner_poly.centroid):
                        main_poly['children'].append({
                            'type': 'polyline',
                            'points': points,
                            'polygon': inner_poly
                        })
                        break
    
    # 步骤3: 返回主要多边形（排样将基于它们进行）
    for main_poly in main_polylines:
        parts.append(main_poly['polygon'])
    
    # 调试输出
    print(f"找到 {len(main_polylines)} 个主要轮廓，共 {len(parts)} 个部件")
    
    return parts, main_polylines  # 返回部件和带有子实体信息的主要多边形