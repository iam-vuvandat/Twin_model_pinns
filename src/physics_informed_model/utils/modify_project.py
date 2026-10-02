import os

def unstick_optimizer():
    base_directory = os.path.dirname(os.path.abspath(__file__))
    project_root_directory = os.path.abspath(os.path.join(base_directory, '..'))
    
    geometry_file_path = os.path.join(project_root_directory, 'geometry_engine', 'geometry.py')
    pinn_architecture_file_path = os.path.join(project_root_directory, 'pinn_architecture.py')
    test_simulation_file_path = os.path.join(project_root_directory, 'test_simulation.py')

    # 1. GIẢM ĐỘ GẮT: steepness từ 5000.0 xuống 300.0
    geometry_source_code = """import torch
from geometry_engine.segment.segment import Segment
from geometry_engine.global_signed_distance_field import compute_global_signed_distance_field
from geometry_engine.global_physical_properties_evaluation import evaluate_global_physical_properties
from geometry_engine.geometry_visualizer import plot_geometry_problem

class Geometry:
    # [CẬP NHẬT]: Steepness = 300.0 giúp vùng giao diện mở rộng ra, mạng nơ-ron dễ dàng nắm bắt đạo hàm
    def __init__(self, steepness=300.0):
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

    # 2. CHUẨN HÓA TỌA ĐỘ: Đưa input (x, y) về phạm vi [-1, 1]
    pinn_architecture_source_code = """import torch
import torch.nn as nn

class PINNArchitecture(nn.Module):
    # [CẬP NHẬT]: Thêm domain_scale = 0.05
    def __init__(self, input_dim=2, hidden_layers=4, hidden_neurons=50, output_dim=1, domain_scale=0.05):
        super().__init__()
        self.domain_scale = domain_scale
        
        layers = []
        layers.append(nn.Linear(input_dim, hidden_neurons))
        layers.append(nn.SiLU())
        
        for _ in range(hidden_layers - 1):
            layers.append(nn.Linear(hidden_neurons, hidden_neurons))
            layers.append(nn.SiLU())
            
        layers.append(nn.Linear(hidden_neurons, output_dim))
        
        self.network = nn.Sequential(*layers)
        self._initialize_weights()

    def _initialize_weights(self):
        for module in self.network:
            if isinstance(module, nn.Linear):
                nn.init.xavier_normal_(module.weight)
                nn.init.zeros_(module.bias)

    def forward(self, xy, sdf_boundary):
        # [CẬP NHẬT CỐT LÕI]: Chuẩn hóa tọa độ. Các trọng số N(0,1) không thể xử lý tọa độ quá nhỏ (0.01)
        xy_normalized = xy / self.domain_scale
        raw_output = self.network(xy_normalized)
        
        A_z = raw_output * sdf_boundary
        return A_z
"""

    # 3. TĂNG ĐIỂM DỮ LIỆU & ADAM EPOCHS
    test_simulation_source_code = """import os
import sys

current_directory = os.path.dirname(os.path.abspath(__file__))
if current_directory not in sys.path:
    sys.path.insert(0, current_directory)

import torch
import numpy as np
import matplotlib.pyplot as plt
from geometry_engine.geometry import Geometry
from geometry_engine.segment.segment import Segment
from physics_domain.collocation_sampler import CollocationSampler
from electro_magnetic_pinn import ElectroMagneticPINN

def main():
    geometry_instance = Geometry()
    
    top_magnet_vertices = [
        [-0.03, 0.015],
        [0.03, 0.015],
        [0.03, 0.025],
        [-0.03, 0.025]
    ]
    top_magnet = Segment(top_magnet_vertices).set_material_properties(
        name="top_magnet",
        relative_permeability=1.05,
        coercive_field_x=800000.0,
        coercive_field_y=0.0
    )
    geometry_instance.add_segment(top_magnet)

    bottom_magnet_vertices = [
        [-0.03, -0.025],
        [0.03, -0.025],
        [0.03, -0.015],
        [-0.03, -0.015]
    ]
    bottom_magnet = Segment(bottom_magnet_vertices).set_material_properties(
        name="bottom_magnet",
        relative_permeability=1.05,
        coercive_field_x=-800000.0,
        coercive_field_y=0.0
    )
    geometry_instance.add_segment(bottom_magnet)
    
    collocation_sampler_instance = CollocationSampler(
        x_boundaries_tuple=(-0.05, 0.05),
        y_boundaries_tuple=(-0.05, 0.05)
    )

    model = ElectroMagneticPINN(
        geometry_engine_instance=geometry_instance,
        collocation_sampler_instance=collocation_sampler_instance
    )
    
    # [CẬP NHẬT CỐT LÕI]: Tăng điểm lấy mẫu và chu kỳ huấn luyện Adam
    model.execute_training_process(
        number_of_uniform_points=2500,     # Tăng từ 200 lên 2500
        number_of_interface_points=800,    # Tăng từ 50 lên 800
        distance_threshold=0.005,
        stages=2,
        epochs_per_stage=400               # Tăng từ 5 lên 400 để Adam có thời gian "làm nóng"
    )
    
    test_points = collocation_sampler_instance.generate_uniform_points_tensor(10)
    predictions = model.predict_magnetic_vector_potential(test_points)
    print("Predicted A_z:\\n", predictions)

if __name__ == '__main__':
    main()
"""

    with open(geometry_file_path, 'w', encoding='utf-8') as f: f.write(geometry_source_code)
    with open(pinn_architecture_file_path, 'w', encoding='utf-8') as f: f.write(pinn_architecture_source_code)
    with open(test_simulation_file_path, 'w', encoding='utf-8') as f: f.write(test_simulation_source_code)
    print("Đã vá lỗi Collocation Aliasing và chuẩn hóa xong!")

if __name__ == '__main__':
    unstick_optimizer()