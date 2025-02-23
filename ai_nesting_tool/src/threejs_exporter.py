import json
import os
from shapely.geometry import Polygon

def export_to_threejs(sheets, sheet_width, sheet_height, output_dir="static"):
    """将排样结果导出为 Three.js 数据"""
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 将数据转换为适合 Three.js 的格式
    data = {}
    try:
        for sheet_idx, parts in sheets.items():
            print(f"Processing sheet {sheet_idx}, parts: {parts}")
            # 将原始坐标列表转换为 Polygon 对象并提取坐标
            polygons = [Polygon(part).exterior.coords[:-1] for part in parts]
            print(f"Polygons for sheet {sheet_idx}: {polygons}")
            data[sheet_idx] = [list(coords) for coords in polygons]
        print(f"Processed data: {data}")
    except Exception as e:
        print(f"转换数据时出错: {e}")
        return None
    
    # 创建 HTML 文件内容，使用最新的 Three.js CDN
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>3D Nesting Visualization</title>
    <style>
        body { margin: 0; overflow: hidden; }
        canvas { display: block; }
        #info {
            position: absolute;
            top: 10px;
            width: 100%;
            text-align: center;
            color: white;
            font-family: Arial, sans-serif;
            z-index: 100;
            background-color: rgba(0,0,0,0.5);
            padding: 5px;
        }
    </style>
</head>
<body>
    <div id="info">3D Nesting Visualization - Use mouse to rotate, zoom and pan</div>
    
    <!-- 使用 CDN 引入 Three.js 最新版本 -->
    <script src="https://cdn.jsdelivr.net/npm/three@0.161.0/build/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.161.0/examples/js/controls/OrbitControls.js"></script>
    
    <script>
        // 板材数据
        const SHEET_WIDTH = SHEET_WIDTH_PLACEHOLDER;
        const SHEET_HEIGHT = SHEET_HEIGHT_PLACEHOLDER;
        const sheetsData = SHEETS_DATA_PLACEHOLDER;
        
        let scene, camera, renderer, controls;
        
        // 初始化 Three.js
        function init() {
            // 创建场景
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0x333333);
            
            // 创建相机
            camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 1, 10000);
            camera.position.set(0, -600, 600);
            camera.up.set(0, 0, 1); // 设置 Z 轴向上
            
            // 创建渲染器
            renderer = new THREE.WebGLRenderer({ antialias: true });
            renderer.setSize(window.innerWidth, window.innerHeight);
            document.body.appendChild(renderer.domElement);
            
            // 添加轨道控制
            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.25;
            controls.screenSpacePanning = false;
            controls.maxPolarAngle = Math.PI / 2;
            
            // 添加灯光
            const ambientLight = new THREE.AmbientLight(0x404040);
            scene.add(ambientLight);
            
            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
            directionalLight.position.set(1, 1, 1);
            scene.add(directionalLight);
            
            // 添加板材和零件
            addSheets();
            
            // 添加坐标轴
            const axesHelper = new THREE.AxesHelper(300);
            scene.add(axesHelper);
            
            // 添加网格
            const gridHelper = new THREE.GridHelper(1000, 10);
            gridHelper.rotation.x = Math.PI / 2;
            scene.add(gridHelper);
            
            // 事件监听
            window.addEventListener('resize', onWindowResize, false);
            
            // 开始动画循环
            animate();
        }
        
        // 添加板材和零件
        function addSheets() {
            let sheetIndex = 0;
            
            for (const [sheetIdx, parts] of Object.entries(sheetsData)) {
                // 创建板材平面
                const sheetGeometry = new THREE.PlaneGeometry(SHEET_WIDTH, SHEET_HEIGHT);
                const sheetMaterial = new THREE.MeshStandardMaterial({ 
                    color: 0xcccccc,
                    side: THREE.DoubleSide,
                    transparent: true,
                    opacity: 0.7
                });
                const sheet = new THREE.Mesh(sheetGeometry, sheetMaterial);
                sheet.position.z = sheetIndex * 20; // 分层显示板材
                scene.add(sheet);
                
                // 创建板材边框
                const borderGeometry = new THREE.EdgesGeometry(sheetGeometry);
                const borderMaterial = new THREE.LineBasicMaterial({ color: 0x888888, linewidth: 2 });
                const border = new THREE.LineSegments(borderGeometry, borderMaterial);
                border.position.z = sheet.position.z;
                scene.add(border);
                
                // 创建零件
                for (const partPoints of parts) {
                    // 创建一个形状
                    const shape = new THREE.Shape();
                    
                    // 确保至少有 3 个点以形成有效多边形
                    if (partPoints.length >= 3) {
                        // 移动到第一个点
                        shape.moveTo(partPoints[0][0], partPoints[0][1]);
                        
                        // 连接其余点
                        for (let i = 1; i < partPoints.length; i++) {
                            shape.lineTo(partPoints[i][0], partPoints[i][1]);
                        }
                        
                        // 闭合路径
                        shape.closePath();
                        
                        // 挤出几何体
                        const extrudeSettings = {
                            depth: 5,
                            bevelEnabled: false
                        };
                        
                        const geometry = new THREE.ExtrudeGeometry(shape, extrudeSettings);
                        const material = new THREE.MeshPhongMaterial({ 
                            color: 0x4285f4,
                            shininess: 100
                        });
                        
                        const part = new THREE.Mesh(geometry, material);
                        part.position.z = sheet.position.z; // 放在当前板材上
                        scene.add(part);
                        
                        // 添加零件边框
                        const edges = new THREE.EdgesGeometry(geometry);
                        const lineMaterial = new THREE.LineBasicMaterial({ color: 0x2a56c6 });
                        const wireframe = new THREE.LineSegments(edges, lineMaterial);
                        wireframe.position.copy(part.position);
                        scene.add(wireframe);
                    }
                }
                
                // 添加标签
                const textCanvas = document.createElement('canvas');
                const context = textCanvas.getContext('2d');
                textCanvas.width = 256;
                textCanvas.height = 64;
                context.fillStyle = 'white';
                context.font = '40px Arial';
                context.fillText(`Sheet ${sheetIdx}`, 10, 40);
                
                const texture = new THREE.CanvasTexture(textCanvas);
                const labelMaterial = new THREE.SpriteMaterial({ map: texture });
                const label = new THREE.Sprite(labelMaterial);
                label.position.set(50, 50, sheet.position.z + 6);
                label.scale.set(100, 25, 1);
                scene.add(label);
                
                sheetIndex++;
            }
            
            // 设置相机位置以查看所有内容
            const center = new THREE.Vector3(SHEET_WIDTH/2, SHEET_HEIGHT/2, sheetIndex * 10);
            controls.target.copy(center);
            
            // 设置相机位置
            camera.position.set(center.x, center.y - 800, center.z + 800);
            camera.lookAt(center);
        }
        
        // 窗口大小改变时调整
        function onWindowResize() {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }
        
        // 动画循环
        function animate() {
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }
        
        // 启动
        init();
    </script>
</body>
</html>
"""

    # 替换占位符
    html_content = html_content.replace('SHEET_WIDTH_PLACEHOLDER', str(sheet_width))
    html_content = html_content.replace('SHEET_HEIGHT_PLACEHOLDER', str(sheet_height))
    html_content = html_content.replace('SHEETS_DATA_PLACEHOLDER', json.dumps(data))
    
    # 保存 HTML 文件
    output_path = os.path.join(output_dir, "nesting_3d_result.html")
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        abs_path = os.path.abspath(output_path)
        print(f"3D结果已保存至: {abs_path}")
        print(f"浏览器访问路径: file:///{abs_path.replace(os.sep, '/')}")
        
        # 验证文件是否存在
        if os.path.exists(output_path):
            print(f"验证成功: 文件已创建 (大小: {os.path.getsize(output_path)} 字节)")
        else:
            print(f"警告: 无法验证文件是否创建成功")
        
        return output_path
    except Exception as e:
        import traceback
        print(f"保存3D结果时出错: {e}")
        print(traceback.format_exc())
        return None