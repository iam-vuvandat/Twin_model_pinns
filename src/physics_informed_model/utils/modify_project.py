import os

def completely_remove_curriculum():
    base_directory = os.path.dirname(os.path.abspath(__file__))
    project_root_directory = os.path.abspath(os.path.join(base_directory, '..'))
    
    electro_magnetic_path = os.path.join(project_root_directory, 'electro_magnetic_pinn.py')
    test_simulation_path = os.path.join(project_root_directory, 'test_simulation.py')
    curriculum_path = os.path.join(project_root_directory, 'curriculum_training_manager.py')

    # Cập nhật ElectroMagneticPINN: Cắt bỏ hoàn toàn Curriculum, gọi thẳng TrainingManager
    electro_magnetic_code = """import torch
from pinn_architecture import PINNArchitecture
from training_manager import TrainingManager
from physics_domain.physical_equations.maxwell_pde_loss import MaxwellPDELoss

class ElectroMagneticPINN:
    def __init__(self, geometry_engine_instance, collocation_sampler_instance):
        self.geometry_engine_instance = geometry_engine_instance
        self.collocation_sampler_instance = collocation_sampler_instance
        
        self.L0 = self.collocation_sampler_instance.x_maximum
        self.H0 = 800000.0
        self.nu0 = self.geometry_engine_instance.vacuum_reluctivity
        self.A0 = (self.H0 * self.L0) / self.nu0
        
        self.pinn_architecture_instance = PINNArchitecture(domain_scale=self.L0)
        self.maxwell_pde_loss_instance = MaxwellPDELoss(L0=self.L0, H0=self.H0, nu0=self.nu0)
        
        self.training_manager_instance = TrainingManager(
            model=self.pinn_architecture_instance,
            pde_evaluator=self.maxwell_pde_loss_instance
        )

    def execute_training_process(self, number_of_uniform_points, number_of_interface_points, distance_threshold, epochs_adam, epochs_lbfgs):
        points_tensor = self.collocation_sampler_instance.generate_combined_points_tensor(
            geometry_object=self.geometry_engine_instance,
            number_of_uniform_points=number_of_uniform_points,
            number_of_interface_points=number_of_interface_points,
            distance_threshold=distance_threshold
        )
        
        physical_properties_dictionary = self.geometry_engine_instance.evaluate_global_physical_properties(points_tensor)
        
        print(f"--- Standard Adam Training ({epochs_adam} Epochs) ---")
        self.training_manager_instance.train_adam(
            epochs=epochs_adam,
            points_tensor=points_tensor,
            reluctivity_tensor=physical_properties_dictionary["reluctivity"],
            current_density_z_tensor=physical_properties_dictionary["current_density_z"],
            coercive_field_x_tensor=physical_properties_dictionary["coercive_field_x"],
            coercive_field_y_tensor=physical_properties_dictionary["coercive_field_y"]
        )
        
        print(f"--- L-BFGS Refinement ({epochs_lbfgs} Epochs) ---")
        self.training_manager_instance.train_lbfgs(
            epochs=epochs_lbfgs, 
            points_tensor=points_tensor, 
            reluctivity_tensor=physical_properties_dictionary["reluctivity"], 
            current_density_z_tensor=physical_properties_dictionary["current_density_z"], 
            coercive_field_x_tensor=physical_properties_dictionary["coercive_field_x"], 
            coercive_field_y_tensor=physical_properties_dictionary["coercive_field_y"]
        )

    def predict_magnetic_vector_potential(self, points_tensor):
        self.pinn_architecture_instance.eval()
        with torch.no_grad():
            A_z_star = self.pinn_architecture_instance(points_tensor)
        return A_z_star * self.A0

    def evaluate_fields(self, points_tensor):
        self.pinn_architecture_instance.eval()
        points_tensor.requires_grad_(True)
        
        A_z_star = self.pinn_architecture_instance(points_tensor)
        A_z_phys = A_z_star * self.A0
        
        grad_A = torch.autograd.grad(
            outputs=A_z_phys,
            inputs=points_tensor,
            grad_outputs=torch.ones_like(A_z_phys),
            create_graph=False,
            retain_graph=False
        )[0]
        
        B_x = grad_A[:, 1:2]
        B_y = -grad_A[:, 0:1]
        
        return A_z_phys.detach(), B_x.detach(), B_y.detach()
"""

    # Cập nhật tham số truyền vào hàm execute_training_process
    test_simulation_code = """import os
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
        epochs_adam=800,
        epochs_lbfgs=100
    )
    
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

    with open(electro_magnetic_path, 'w', encoding='utf-8') as f:
        f.write(electro_magnetic_code)
        
    with open(test_simulation_path, 'w', encoding='utf-8') as f:
        f.write(test_simulation_code)
        
    # Xóa vĩnh viễn file curriculum
    if os.path.exists(curriculum_path):
        os.remove(curriculum_path)
        
    print("Đã dọn dẹp hoàn toàn Curriculum Training. Mô hình sẽ chạy với 100% từ hóa ngay từ đầu.")

if __name__ == '__main__':
    completely_remove_curriculum()