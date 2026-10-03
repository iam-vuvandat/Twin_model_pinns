import os

def execute_scenario_1_autograd_and_seed():
    base_directory = os.path.dirname(os.path.abspath(__file__))
    project_root_directory = os.path.abspath(os.path.join(base_directory, '..'))
    
    training_manager_path = os.path.join(project_root_directory, 'training_manager.py')
    curriculum_path = os.path.join(project_root_directory, 'curriculum_training_manager.py')
    pinn_path = os.path.join(project_root_directory, 'electro_magnetic_pinn.py')
    test_path = os.path.join(project_root_directory, 'test_simulation.py')

    # 1. Cập nhật TrainingManager: Đưa tính toán vật lý vào trong compute_loss để giải phóng VRAM
    training_manager_source_code = """import torch
import torch.optim as optim

class TrainingManager:
    def __init__(self, model, pde_evaluator, geometry_engine_instance, lr_adam=1e-3):
        self.model = model
        self.pde_evaluator = pde_evaluator
        self.geometry_engine_instance = geometry_engine_instance
        
        self.optimizer_adam = optim.Adam(self.model.parameters(), lr=lr_adam)
        
        self.optimizer_lbfgs = optim.LBFGS(
            self.model.parameters(),
            lr=1.0,
            max_iter=50,
            max_eval=50,
            tolerance_grad=1e-7,
            tolerance_change=1e-9,
            history_size=100,
            line_search_fn="strong_wolfe"
        )

    def compute_loss(self, points_tensor, alpha=1.0):
        # Tính toán thuộc tính vật lý động (dynamic) để đồ thị đạo hàm được khởi tạo và hủy gọn gàng trong 1 epoch
        phys_props = self.geometry_engine_instance.evaluate_global_physical_properties(points_tensor)
        nu = phys_props["reluctivity"]
        J_z = phys_props["current_density_z"] * alpha
        H_cx = phys_props["coercive_field_x"] * alpha
        H_cy = phys_props["coercive_field_y"] * alpha

        A_z_star = self.model(points_tensor)
        
        residual_star = self.pde_evaluator.compute_residual(
            xy=points_tensor,
            A_z_star=A_z_star,
            nu=nu,
            J_z=J_z,
            H_cx=H_cx,
            H_cy=H_cy
        )
        
        loss_pde = torch.mean(residual_star**2)
        return loss_pde

    def train_adam(self, epochs, points_tensor, alpha):
        self.model.train()
        best_loss = float('inf')
        best_model_state = {key: value.cpu().clone() for key, value in self.model.state_dict().items()}
        
        scheduler_adam = optim.lr_scheduler.CosineAnnealingLR(self.optimizer_adam, T_max=epochs, eta_min=1e-6)
        
        for epoch in range(epochs):
            self.optimizer_adam.zero_grad()
            
            loss = self.compute_loss(points_tensor, alpha)
            
            if torch.isnan(loss) or loss.item() > 10.0 * best_loss:
                self.model.load_state_dict(best_model_state)
                for param_group in self.optimizer_adam.param_groups:
                    param_group['lr'] *= 0.8
                continue
                
            # ĐÃ XÓA retain_graph=True. Giải phóng VRAM hoàn toàn!
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            self.optimizer_adam.step()
            scheduler_adam.step()
            
            current_loss_value = loss.item()
            if current_loss_value < best_loss:
                best_loss = current_loss_value
                best_model_state = {key: value.cpu().clone() for key, value in self.model.state_dict().items()}
            
            if (epoch + 1) % 100 == 0:
                current_lr = self.optimizer_adam.param_groups[0]['lr']
                print(f"Adam Epoch {epoch + 1}: Loss = {current_loss_value:.6e} | LR = {current_lr:.3e}")

    def train_lbfgs(self, epochs, points_tensor, alpha):
        self.model.train()
        for epoch in range(epochs):
            def closure():
                self.optimizer_lbfgs.zero_grad()
                loss = self.compute_loss(points_tensor, alpha)
                loss.backward()
                return loss
            
            loss_val = self.optimizer_lbfgs.step(closure)
            print(f"L-BFGS Epoch {epoch + 1}: Loss = {loss_val.item():.6e}")
"""

    # 2. Cập nhật Curriculum: Loại bỏ việc truyền tensor tĩnh
    curriculum_source_code = """import torch
from training_manager import TrainingManager

class CurriculumTrainingManager:
    def __init__(self, training_manager_instance: TrainingManager):
        self.training_manager_instance = training_manager_instance

    def train_source_ramping(self, stages, epochs_per_stage, points_tensor):
        for stage in range(1, stages + 1):
            alpha = stage / stages
            print(f"--- Curriculum Stage {stage}/{stages} (Alpha = {alpha:.2f}) ---")
            
            self.training_manager_instance.train_adam(
                epochs=epochs_per_stage,
                points_tensor=points_tensor,
                alpha=alpha
            )
            
        print("--- Curriculum L-BFGS Refinement (Alpha = 1.00) ---")
        
        self.training_manager_instance.train_lbfgs(
            epochs=100, 
            points_tensor=points_tensor, 
            alpha=1.0
        )
"""

    # 3. Cập nhật PINN: Bổ sung liên kết geometry_engine cho TrainingManager
    pinn_source_code = """import torch
from pinn_architecture import PINNArchitecture
from training_manager import TrainingManager
from curriculum_training_manager import CurriculumTrainingManager
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
            pde_evaluator=self.maxwell_pde_loss_instance,
            geometry_engine_instance=self.geometry_engine_instance
        )
        
        self.curriculum_training_manager_instance = CurriculumTrainingManager(
            training_manager_instance=self.training_manager_instance
        )

    def execute_training_process(self, number_of_uniform_points, number_of_interface_points, distance_threshold, stages, epochs_per_stage):
        points_tensor = self.collocation_sampler_instance.generate_combined_points_tensor(
            geometry_object=self.geometry_engine_instance,
            number_of_uniform_points=number_of_uniform_points,
            number_of_interface_points=number_of_interface_points,
            distance_threshold=distance_threshold
        )
        
        # Chỉ cần truyền points_tensor, các thuộc tính vật lý sẽ được tính động bên trong
        self.curriculum_training_manager_instance.train_source_ramping(
            stages=stages,
            epochs_per_stage=epochs_per_stage,
            points_tensor=points_tensor
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

    # 4. Cập nhật Test: Bổ sung Global Seed
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

# Tích hợp Global Seed đảm bảo tính Reproducibility
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

    with open(training_manager_path, 'w', encoding='utf-8') as f: f.write(training_manager_source_code)
    with open(curriculum_path, 'w', encoding='utf-8') as f: f.write(curriculum_source_code)
    with open(pinn_path, 'w', encoding='utf-8') as f: f.write(pinn_source_code)
    with open(test_path, 'w', encoding='utf-8') as f: f.write(test_source_code)
        
    print("Hoàn tất Kịch bản 1: Giải phóng VRAM, loại bỏ retain_graph và cấu hình Global Seed!")

if __name__ == '__main__':
    execute_scenario_1_autograd_and_seed()