from shapely.geometry import Polygon

def calculate_area(polygon: Polygon):
    """计算多边形面积"""
    return polygon.area