import os

def fix_imports():
    """
    Hàm này dùng để sửa các lỗi đường dẫn import ngầm định 
    trong cấu trúc dự án physics_informed_model.
    """
    
    # 1. Xác định gốc thư mục
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(base_dir, '..'))
    
    print(f"Đang tiến hành kiểm tra và sửa lỗi import tại: {project_root}")

    # =========================================================================
    # SỬA LỖI 1: curriculum_training_manager.py
    # Lỗi: import .training_manager (tương đối nhưng có thể gây lỗi nếu chạy trực tiếp)
    # Sửa thành: import training_manager (trong cùng một cấp của sys.path được nạp vào)
    # =========================================================================
    curriculum_file = os.path.join(project_root, 'curriculum_training_manager.py')
    if os.path.exists(curriculum_file):
        with open(curriculum_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Sửa import
        new_content = content.replace("from .training_manager import TrainingManager", "from training_manager import TrainingManager")
        
        with open(curriculum_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Đã sửa: curriculum_training_manager.py")
    else:
        print("Không tìm thấy: curriculum_training_manager.py")


    # =========================================================================
    # SỬA LỖI 2: u_shape_magnet_template.py
    # Lỗi: gọi 'from src.physics_informed_model.geometry_engine.geometry import Polygon'
    # nhưng thư mục chứa nó đã bị thao túng 'sys.path.append(...)'. Cần dùng import tương đối.
    # =========================================================================
    template_file = os.path.join(project_root, 'geometry_engine', 'templates', 'u_shape_magnet_template.py')
    if os.path.exists(template_file):
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Thay thế khối sys.path và import cứng nhắc bằng import tương đối trỏ lên 1 cấp
        old_import_block = """import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

import torch
from src.physics_informed_model.geometry_engine.geometry import Polygon"""

        new_import_block = """import torch
from ..geometry import Polygon"""

        new_content = content.replace(old_import_block, new_import_block)
        
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Đã sửa: u_shape_magnet_template.py")
    else:
        print("Không tìm thấy: u_shape_magnet_template.py")

    print("Hoàn tất sửa lỗi import!")

if __name__ == "__main__":
    fix_imports()