import os

def update_smooth_interface():
    base_directory = os.path.dirname(os.path.abspath(__file__))
    project_root_directory = os.path.abspath(os.path.join(base_directory, '..'))
    
    geometry_engine_directory = os.path.join(project_root_directory, 'geometry_engine')
    
    # 1. Đường dẫn 2 tệp cần cập nhật
    global_properties_file_path = os.path.join(geometry_engine_directory, 'global_physical_properties_evaluation.py')
    geometry_file_path = os.path.join(geometry_engine_directory, 'geometry.py')

    # 2. Cập nhật cơ chế pha trộn vật lý (Smooth Masking)
    global_properties_source_code = """import torch

def evaluate_global_physical_properties(segments_list, points_tensor, vacuum_reluctivity, steepness=5000.0):
    number_of_points = points_tensor.shape[0]
    computation_device = points_tensor.device
    
    # Khởi tạo không gian nền mặc định (Background) là Không khí
    global_reluctivity_tensor = torch.full((number_of_points, 1), vacuum_reluctivity, dtype=torch.float32, device=computation_device)
    global_coercive_field_x_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)
    global_coercive_field_y_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)
    global_current_density_z_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)
    global_material_classification_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)

    material_index_counter = 1.0

    for segment_object in segments_list:
        signed_distance_field = segment_object.compute_signed_distance_field(points_tensor)
        
        # [CẬP NHẬT CỐT LÕI]: Hàm Sigmoid làm mờ ranh giới, giữ lại đạo hàm cho PyTorch Autograd
        mask_smooth = torch.sigmoid(-steepness * signed_distance_field)
        
        # Tính toán giá trị của riêng Segment
        seg_reluctivity = segment_object.evaluate_reluctivity(points_tensor)
        hx_tensor, hy_tensor = segment_object.evaluate_magnetization_vector(points_tensor)
        seg_jz = segment_object.evaluate_current_density(points_tensor)
        
        # Phối trộn (Blend) lên ma trận nền dựa vào hệ số mặt nạ
        global_reluctivity_tensor = global_reluctivity_tensor + mask_smooth * (seg_reluctivity - vacuum_reluctivity)
        global_coercive_field_x_tensor = global_coercive_field_x_tensor + mask_smooth * hx_tensor
        global_coercive_field_y_tensor = global_coercive_field_y_tensor + mask_smooth * hy_tensor
        global_current_density_z_tensor = global_current_density_z_tensor + mask_smooth * seg_jz
        
        global_material_classification_tensor = global_material_classification_tensor + mask_smooth * material_index_counter
        
        material_index_counter += 1.0

    return {
        "reluctivity": global_reluctivity_tensor,
        "coercive_field_x": global_coercive_field_x_tensor,
        "coercive_field_y": global_coercive_field_y_tensor,
        "current_density_z": global_current_density_z_tensor,
        "material_classification": global_material_classification_tensor
    }
"""

    # 3. Cập nhật lớp Geometry để truyền tham số steepness
    geometry_source_code = """import torch
from geometry_engine.segment.segment import Segment
from geometry_engine.global_signed_distance_field import compute_global_signed_distance_field
from geometry_engine.global_physical_properties_evaluation import evaluate_global_physical_properties
from geometry_engine.geometry_visualizer import plot_geometry_problem

class Geometry:
    def __init__(self, steepness=5000.0):
        self.segments_list = []
        self.vacuum_reluctivity = 795774.715459
        self.steepness = steepness

    def add_segment(self, segment_object):
        self.segments_list.append(segment_object)
        return self

    def compute_global_signed_distance_field(self, points_tensor):
        return compute_global_signed_distance_field(self.segments_list, points_tensor)

    def evaluate_global_physical_properties(self, points_tensor):
        return evaluate_global_physical_properties(self.segments_list, points_tensor, self.vacuum_reluctivity, self.steepness)

    def plot_problem_definition(self, x_boundaries_tuple, y_boundaries_tuple, resolution=100):
        plot_geometry_problem(self, x_boundaries_tuple, y_boundaries_tuple, resolution)
"""

    with open(global_properties_file_path, 'w', encoding='utf-8') as f:
        f.write(global_properties_source_code)
        
    with open(geometry_file_path, 'w', encoding='utf-8') as f:
        f.write(geometry_source_code)

    print("Đã cập nhật hệ thống Giao diện mờ (Smooth Interface) thành công!")

if __name__ == '__main__':
    update_smooth_interface()