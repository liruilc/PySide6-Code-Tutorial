def generate_gcode(sheets, transformed_entities=None, file_path="output.nc"):
    """将排样结果转换为 G 代码，支持处理子实体"""
    gcode = ["G21", "G90"]  # 毫米单位，绝对定位
    
    if transformed_entities:
        # 使用包含子实体信息的完整数据
        for sheet_idx, entities in transformed_entities.items():
            gcode.append(f"(Sheet {sheet_idx})")
            gcode.append("G00 Z5.0")
            
            for entity in entities:
                # 处理主轮廓
                main_part = entity['main']
                coords = list(main_part.exterior.coords)[:-1]
                gcode.append(f"G00 X{coords[0][0]:.2f} Y{coords[0][1]:.2f}")
                gcode.append("G01 Z-2.0 F500")
                for x, y in coords[1:]:
                    gcode.append(f"G01 X{x:.2f} Y{y:.2f} F1000")
                gcode.append(f"G01 X{coords[0][0]:.2f} Y{coords[0][1]:.2f}")
                gcode.append("G00 Z5.0")
                
                # 处理子实体（例如孔）
                for child in entity['children']:
                    if child['type'] == 'circle':
                        x, y = child['center']
                        r = child['radius']
                        gcode.append(f"G00 X{x:.2f} Y{y:.2f}")
                        gcode.append("G01 Z-2.0 F500")
                        # 添加圆的G代码（可以使用G02/G03命令）
                        gcode.append(f"G03 X{x:.2f} Y{y:.2f} I{r:.2f} J0 F800")  # 顺时针完整圆弧
                        gcode.append("G00 Z5.0")
                    elif child['type'] == 'polyline':
                        child_coords = list(child['polygon'].exterior.coords)[:-1]
                        gcode.append(f"G00 X{child_coords[0][0]:.2f} Y{child_coords[0][1]:.2f}")
                        gcode.append("G01 Z-2.0 F500")
                        for x, y in child_coords[1:]:
                            gcode.append(f"G01 X{x:.2f} Y{y:.2f} F1000")
                        gcode.append(f"G01 X{child_coords[0][0]:.2f} Y{child_coords[0][1]:.2f}")
                        gcode.append("G00 Z5.0")
    else:
        # 原始逻辑，只处理外部轮廓
        for sheet_idx, parts in sheets.items():
            gcode.append(f"(Sheet {sheet_idx})")
            gcode.append("G00 Z5.0")
            for part in parts:
                coords = list(part.exterior.coords)[:-1]
                gcode.append(f"G00 X{coords[0][0]:.2f} Y{coords[0][1]:.2f}")
                gcode.append("G01 Z-2.0 F500")
                for x, y in coords[1:]:
                    gcode.append(f"G01 X{x:.2f} Y{y:.2f} F1000")
                gcode.append(f"G01 X{coords[0][0]:.2f} Y{coords[0][1]:.2f}")
                gcode.append("G00 Z5.0")
                
    with open(file_path, "w") as f:
        f.write("\n".join(gcode))
    return file_path