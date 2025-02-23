import sys
import os
import webbrowser
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                              QWidget, QPushButton, QFileDialog, QLabel, QProgressBar,
                              QMessageBox)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt, QTimer, QUrl
import json
import threading

# 修改导入方式
from . import dxf_parser
from . import nesting_optimizer
from . import gcode_generator
from . import threejs_exporter

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.dxf_path = None
        self.threejs_path = None
        self.optimizer = None  # 添加 optimizer 属性
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("AI Nesting Tool")
        self.setGeometry(100, 100, 1200, 800)  # 增大窗口以适应 3D 视图
        
        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1E1E1E;
            }
            QWidget {
                color: white;
            }
            QPushButton {
                background-color: #2196F3;
                border: none;
                border-radius: 5px;
                padding: 10px;
                min-width: 120px;
                color: white;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QLabel {
                color: white;
            }
        """)
        
        # 创建中央控件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 创建标题
        title = QLabel("AI Nesting Tool")
        title.setStyleSheet("font-size: 32px; font-weight: bold; margin: 20px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 创建文件选择区域
        self.file_label = QLabel("No file selected")
        self.file_label.setAlignment(Qt.AlignCenter)
        
        select_button = QPushButton("Select DXF File")
        select_button.clicked.connect(self.select_file)
        
        layout.addWidget(select_button)
        layout.addWidget(self.file_label)
        
        # 创建运行按钮
        run_button = QPushButton("Run AI Nesting")
        run_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                min-height: 50px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        run_button.clicked.connect(self.run_nesting)
        layout.addWidget(run_button)
        
        # 创建进度条
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        # 结果区域
        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout(self.results_widget)
        layout.addWidget(self.results_widget)
        
        # 添加 QWebEngineView 用于显示 3D 可视化
        self.web_view = QWebEngineView()
        self.web_view.setMinimumHeight(400)  # 设置最小高度以确保可见
        layout.addWidget(self.web_view)
        layout.addStretch()  # 添加弹性空间，让布局更灵活
    
    def select_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select DXF File", "", "DXF Files (*.dxf)")
        if filename:
            self.dxf_path = filename
            self.file_label.setText(f"Selected: {os.path.basename(filename)}")
    
    def run_nesting(self):
        if not self.dxf_path:
            QMessageBox.warning(self, "Warning", "Please select a DXF file first.")
            return
        
        self.progress.setRange(0, 0)  # 设置为忙碌状态
        self.progress.setVisible(True)
        
        # 启动处理线程
        threading.Thread(target=self.process_nesting, daemon=True).start()
    
    def process_nesting(self):
        try:
            # 加载和处理 DXF 文件
            parts_data = dxf_parser.parse_dxf(self.dxf_path)
            print(f"Parts loaded: {len(parts_data[0])}")
            
            # 优化排样
            sheet_width, sheet_height = 1200, 1200
            self.optimizer = nesting_optimizer.NestingOptimizer(parts_data[0], sheet_width, sheet_height)
            solution = self.optimizer.genetic_algorithm()
            
            # 调试信息
            print("Sheets details:")
            for sheet_idx, parts in self.optimizer.sheets.items():
                print(f"Sheet {sheet_idx}:")
                for i, part in enumerate(parts):
                    print(f"  Part {i+1}: Type={type(part)}, Area={part.area}, Centroid={part.centroid}")
            
            # 生成输出
            gcode_path = gcode_generator.generate_gcode(self.optimizer.sheets, self.optimizer.transformed_entities)
            self.threejs_path = threejs_exporter.export_to_threejs(self.optimizer.sheets, sheet_width, sheet_height)
            
            # 在主线程中更新 UI 和 3D 视图
            QTimer.singleShot(0, self.update_results)
            QTimer.singleShot(0, self.load_3d_view)
            
        except Exception as e:
            import traceback
            print(f"Error during nesting: {e}")
            print(traceback.format_exc())
            QTimer.singleShot(0, lambda: QMessageBox.critical(self, "Error", str(e)))
        finally:
            QTimer.singleShot(0, lambda: self.progress.setVisible(False))
    
    def update_results(self):
        # 清除旧的结果
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 显示板材信息
        for sheet_idx, parts in self.optimizer.sheets.items():
            sheet_info = QLabel(f"Sheet {sheet_idx}")
            sheet_info.setStyleSheet("font-size: 16px; font-weight: bold;")
            self.results_layout.addWidget(sheet_info)
            
            for i, part in enumerate(parts):
                try:
                    part_info = QLabel(
                        f"Part {i+1}: "
                        f"Area = {part.area:.2f}, "
                        f"Center = ({part.centroid.x:.2f}, {part.centroid.y:.2f})"
                    )
                    self.results_layout.addWidget(part_info)
                except Exception as e:
                    error_info = QLabel(f"Error processing part {i+1}: {str(e)}")
                    error_info.setStyleSheet("color: red;")
                    self.results_layout.addWidget(error_info)
                    print(f"Part {i+1} details: {type(part)}, {part}")
    
    def load_3d_view(self):
        if not self.threejs_path:
            print("No 3D result file available to load.")
            return
        
        try:
            print(f"Attempting to load 3D view from: {self.threejs_path}")
            html_url = QUrl.fromLocalFile(self.threejs_path)
            self.web_view.setUrl(html_url)
            print(f"Loaded 3D view from: {self.threejs_path}")
        except Exception as e:
            print(f"Failed to load 3D view: {e}")
            QMessageBox.warning(self, "3D View Error", f"Unable to load 3D view: {str(e)}")

def create_ui():
    """创建并运行 UI"""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()

if __name__ == '__main__':
    sys.exit(create_ui())