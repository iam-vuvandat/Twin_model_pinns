import os

def execute_scenario_4_material_priority_and_blending():
    base_directory = os.path.dirname(os.path.abspath(__file__))
    project_root_directory = os.path.abspath(os.path.join(base_directory, '..'))
    
    segment_path = os.path.join(project_root_directory, 'geometry_engine', 'segment', 'segment.py')
    global_eval_path = os.path.join(project_root_directory, 'geometry_engine', 'global_physical_properties_evaluation.py')
    test_path = os.path.join(project_root_directory, 'test_simulation.py')

    # 1. Cập nhật Segment: Thêm thuộc tính priority
    segment_source_code = """import torch
from geometry_engine.segment.polygon_signed_distance_field import compute_polygon_signed_distance_field

class Segment:
    def __init__(self, vertices_list=None):
        self.material_name = "air"
        self.vacuum_reluctivity = 795774.715459
        self.priority = 0
        
        self.relative_permeability = 1.0
        self.reluctivity_function = None
        
        self.coercive_field_x = 0.0
        self.coercive_field_y = 0.0
        self.magnetization_vector_function = None
        
        self.current_density_z_axis = 0.0
        self.current_density_function = None
        
        self.vertices_tensor = None
        if vertices_list is not None:
            self.set_vertices(vertices_list)

    def set_vertices(self, vertices_list):
        self.vertices_tensor = torch.tensor(vertices_list, dtype=torch.float32)
        return self

    def set_material_properties(
        self, 
        name="default",
        priority=0,
        relative_permeability=1.0, 
        reluctivity_function=None,
        coercive_field_x=0.0,
        coercive_field_y=0.0,
        magnetization_vector_function=None, 
        current_density_z_axis=0.0,
        current_density_function=None
    ):
        self.material_name = name
        self.priority = priority
        self.relative_permeability = relative_permeability
        self.reluctivity_function = reluctivity_function
        self.coercive_field_x = coercive_field_x
        self.coercive_field_y = coercive_field_y
        self.magnetization_vector_function = magnetization_vector_function
        self.current_density_z_axis = current_density_z_axis
        self.current_density_function = current_density_function
        return self

    def compute_signed_distance_field(self, points_tensor):
        return compute_polygon_signed_distance_field(self.vertices_tensor, points_tensor)

    def evaluate_reluctivity(self, points_tensor):
        if self.reluctivity_function is not None:
            return self.reluctivity_function(points_tensor)
        constant_reluctivity = self.vacuum_reluctivity / self.relative_permeability
        return torch.full((points_tensor.shape[0], 1), constant_reluctivity, dtype=torch.float32, device=points_tensor.device)

    def evaluate_magnetization_vector(self, points_tensor):
        if self.magnetization_vector_function is not None:
            return self.magnetization_vector_function(points_tensor)
        hx_tensor = torch.full((points_tensor.shape[0], 1), self.coercive_field_x, dtype=torch.float32, device=points_tensor.device)
        hy_tensor = torch.full((points_tensor.shape[0], 1), self.coercive_field_y, dtype=torch.float32, device=points_tensor.device)
        return hx_tensor, hy_tensor

    def evaluate_current_density(self, points_tensor):
        if self.current_density_function is not None:
            return self.current_density_function(points_tensor)
        return torch.full((points_tensor.shape[0], 1), self.current_density_z_axis, dtype=torch.float32, device=points_tensor.device)
"""

    # 2. Cập nhật Global Physical Properties: Sắp xếp theo priority và dùng Alpha Compositing
    global_eval_source_code = """import torch

def evaluate_global_physical_properties(segments_list, points_tensor, vacuum_reluctivity, steepness=5000.0):
    number_of_points = points_tensor.shape[0]
    computation_device = points_tensor.device
    
    global_reluctivity_tensor = torch.full((number_of_points, 1), vacuum_reluctivity, dtype=torch.float32, device=computation_device)
    global_coercive_field_x_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)
    global_coercive_field_y_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)
    global_current_density_z_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)
    global_material_classification_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)

    sorted_segments = sorted(segments_list, key=lambda s: s.priority)
    material_index_counter = 1.0

    for segment_object in sorted_segments:
        signed_distance_field = segment_object.compute_signed_distance_field(points_tensor)
        
        mask_smooth = torch.sigmoid(-steepness * signed_distance_field).view(-1, 1)
        
        seg_reluctivity = segment_object.evaluate_reluctivity(points_tensor)
        hx_tensor, hy_tensor = segment_object.evaluate_magnetization_vector(points_tensor)
        seg_jz = segment_object.evaluate_current_density(points_tensor)
        
        inv_mask = 1.0 - mask_smooth
        global_reluctivity_tensor = global_reluctivity_tensor * inv_mask + seg_reluctivity * mask_smooth
        global_coercive_field_x_tensor = global_coercive_field_x_tensor * inv_mask + hx_tensor * mask_smooth
        global_coercive_field_y_tensor = global_coercive_field_y_tensor * inv_mask + hy_tensor * mask_smooth
        global_current_density_z_tensor = global_current_density_z_tensor * inv_mask + seg_jz * mask_smooth
        
        global_material_classification_tensor = global_material_classification_tensor * inv_mask + material_index_counter * mask_smooth
        
        material_index_counter += 1.0

    return {
        "reluctivity": global_reluctivity_tensor,
        "coercive_field_x": global_coercive_field_x_tensor,
        "coercive_field_y": global_coercive_field_y_tensor,
        "current_density_z": global_current_density_z_tensor,
        "material_classification": global_material_classification_tensor
    }
"""

    # 3. Cập nhật Test: Bổ sung priority=1 cho các nam châm để ghi đè lên background (không khí)
    test_source_code = """import os
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

GLOBAL_SEED = 42
torch.manual_seed(GLOBAL_SEED)
np.random.seed(GLOBAL_SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(GLOBAL_SEED)

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
        priority=1,
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
        priority=1,
        relative_permeability=1.05,
        coercive_field_x=800000.0,
        coercive_field_y=0.0
    )
    geometry_instance.add_segment(bottom_magnet)
    
    collocation_sampler_instance = CollocationSampler(
        x_boundaries_tuple=(-0.05, 0.05),
        y_boundaries_tuple=(-0.05, 0.05)
    )

    geometry_instance.plot_problem_definition(
        x_boundaries_tuple=(-0.05, 0.05),
        y_boundaries_tuple=(-0.05, 0.05),
        resolution=100
    )

    model = ElectroMagneticPINN(
        geometry_engine_instance=geometry_instance,
        collocation_sampler_instance=collocation_sampler_instance
    )
    
    model.execute_training_process(
        number_of_uniform_points=2500,
        number_of_interface_points=800,
        distance_threshold=0.005,
        stages=2,
        epochs_per_stage=400
    )
    
    print("\\n--- KẾT QUẢ CHẨN ĐOÁN (DIAGNOSTICS) ---")
    diagnostics = model.evaluate_diagnostics(number_of_points=10000)
    print(f"Số dư Maxwell RMS (R_RMS): {diagnostics['R_RMS']:.6e}")
    print(f"Số dư cực đại (R_max):    {diagnostics['R_max']:.6e}")
    print(f"Sai số rò rỉ biên (E_b):  {diagnostics['E_boundary']:.6e} Wb/m")
    print("---------------------------------------\\n")
    
    print("Đang tạo biểu đồ trực quan hóa kết quả trường điện từ...")
    resolution = 120
    x_coords = np.linspace(-0.05, 0.05, resolution)
    y_coords = np.linspace(-0.05, 0.05, resolution)
    X_grid, Y_grid = np.meshgrid(x_coords, y_coords)
    
    xy_points_tensor = torch.tensor(np.column_stack((X_grid.ravel(), Y_grid.ravel())), dtype=torch.float32)
    
    A_z_pred, B_x_pred, B_y_pred = model.evaluate_fields(xy_points_tensor)
    
    A_z_grid = A_z_pred.numpy().reshape(resolution, resolution)
    B_x_grid = B_x_pred.numpy().reshape(resolution, resolution)
    B_y_grid = B_y_pred.numpy().reshape(resolution, resolution)
    B_mag_grid = np.sqrt(B_x_grid**2 + B_y_grid**2)
    
    fig, axs = plt.subplots(2, 2, figsize=(12, 10))
    
    contour_az = axs[0, 0].contourf(X_grid, Y_grid, A_z_grid, levels=60, cmap="jet")
    fig.colorbar(contour_az, ax=axs[0, 0], label="A_z (Wb/m)")
    axs[0, 0].set_title("Magnetic Vector Potential ($A_z$)")
    axs[0, 0].set_xlabel("x (m)")
    axs[0, 0].set_ylabel("y (m)")
    axs[0, 0].set_aspect('equal')
    
    contour_b = axs[0, 1].contourf(X_grid, Y_grid, B_mag_grid, levels=60, cmap="rainbow")
    fig.colorbar(contour_b, ax=axs[0, 1], label="|B| (T)")
    axs[0, 1].set_title("Magnetic Flux Density Magnitude ($|B|$)")
    axs[0, 1].set_xlabel("x (m)")
    axs[0, 1].set_ylabel("y (m)")
    axs[0, 1].set_aspect('equal')
    
    contour_bx = axs[1, 0].contourf(X_grid, Y_grid, B_x_grid, levels=60, cmap="coolwarm")
    fig.colorbar(contour_bx, ax=axs[1, 0], label="B_x (T)")
    axs[1, 0].set_title("Magnetic Field Component ($B_x$)")
    axs[1, 0].set_xlabel("x (m)")
    axs[1, 0].set_ylabel("y (m)")
    axs[1, 0].set_aspect('equal')
    
    contour_by = axs[1, 1].contourf(X_grid, Y_grid, B_y_grid, levels=60, cmap="coolwarm")
    fig.colorbar(contour_by, ax=axs[1, 1], label="B_y (T)")
    axs[1, 1].set_title("Magnetic Field Component ($B_y$)")
    axs[1, 1].set_xlabel("x (m)")
    axs[1, 1].set_ylabel("y (m)")
    axs[1, 1].set_aspect('equal')
    
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    main()
"""

    with open(segment_path, 'w', encoding='utf-8') as f: f.write(segment_source_code)
    with open(global_eval_path, 'w', encoding='utf-8') as f: f.write(global_eval_source_code)
    with open(test_path, 'w', encoding='utf-8') as f: f.write(test_source_code)
        
    print("Hoàn tất Kịch bản 4: Tích hợp Material Priority và Alpha Compositing!")

if __name__ == '__main__':
    execute_scenario_4_material_priority_and_blending()