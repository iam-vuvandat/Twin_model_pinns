import os

def execute_scenario_3_diagnostics_and_checkpointing():
    base_directory = os.path.dirname(os.path.abspath(__file__))
    project_root_directory = os.path.abspath(os.path.join(base_directory, '..'))
    
    training_manager_path = os.path.join(project_root_directory, 'training_manager.py')
    electro_magnetic_path = os.path.join(project_root_directory, 'electro_magnetic_pinn.py')
    test_path = os.path.join(project_root_directory, 'test_simulation.py')

    # 1. Cập nhật TrainingManager: Thêm history, best_model_state và last_model_state
    training_manager_source_code = """import torch
import torch.optim as optim
import copy

class TrainingManager:
    def __init__(self, model, pde_evaluator, geometry_engine_instance, lr_adam=1e-3):
        self.model = model
        self.pde_evaluator = pde_evaluator
        self.geometry_engine_instance = geometry_engine_instance
        
        # [CẬP NHẬT] Thêm bộ nhớ lưu trữ lịch sử và checkpoint
        self.loss_history = []
        self.best_model_state = None
        self.last_model_state = None
        
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
        if self.best_model_state is None:
            self.best_model_state = copy.deepcopy(self.model.state_dict())
        
        scheduler_adam = optim.lr_scheduler.CosineAnnealingLR(self.optimizer_adam, T_max=epochs, eta_min=1e-6)
        
        for epoch in range(epochs):
            self.optimizer_adam.zero_grad()
            
            loss = self.compute_loss(points_tensor, alpha)
            
            if torch.isnan(loss) or loss.item() > 10.0 * best_loss:
                self.model.load_state_dict(self.best_model_state)
                for param_group in self.optimizer_adam.param_groups:
                    param_group['lr'] *= 0.8
                continue
                
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            self.optimizer_adam.step()
            scheduler_adam.step()
            
            current_loss_value = loss.item()
            self.loss_history.append(current_loss_value)
            
            if current_loss_value < best_loss:
                best_loss = current_loss_value
                self.best_model_state = copy.deepcopy(self.model.state_dict())
            
            if (epoch + 1) % 100 == 0:
                current_lr = self.optimizer_adam.param_groups[0]['lr']
                print(f"Adam Epoch {epoch + 1}: Loss = {current_loss_value:.6e} | LR = {current_lr:.3e}")
                
        self.last_model_state = copy.deepcopy(self.model.state_dict())

    def train_lbfgs(self, epochs, points_tensor, alpha):
        self.model.train()
        for epoch in range(epochs):
            def closure():
                self.optimizer_lbfgs.zero_grad()
                loss = self.compute_loss(points_tensor, alpha)
                loss.backward()
                return loss
            
            loss_val = self.optimizer_lbfgs.step(closure)
            current_loss_value = loss_val.item()
            self.loss_history.append(current_loss_value)
            self.last_model_state = copy.deepcopy(self.model.state_dict())
            
            print(f"L-BFGS Epoch {epoch + 1}: Loss = {current_loss_value:.6e}")
"""

    # 2. Cập nhật ElectroMagneticPINN: Thêm hàm evaluate_diagnostics()
    electro_magnetic_source_code = """import torch
from pinn_architecture import PINNArchitecture
from training_manager import TrainingManager
from curriculum_training_manager import CurriculumTrainingManager
from physics_domain.physical_equations.maxwell_pde_loss import MaxwellPDELoss

class ElectroMagneticPINN:
    def __init__(self, geometry_engine_instance, collocation_sampler_instance):
        self.geometry_engine_instance = geometry_engine_instance
        self.collocation_sampler_instance = collocation_sampler_instance
        
        self.L0 = max(abs(self.collocation_sampler_instance.x_maximum), abs(self.collocation_sampler_instance.x_minimum))
        self.H0 = 800000.0
        self.nu0 = self.geometry_engine_instance.vacuum_reluctivity
        self.A0 = (self.H0 * self.L0) / self.nu0
        
        self.pinn_architecture_instance = PINNArchitecture(
            x_bounds=(self.collocation_sampler_instance.x_minimum, self.collocation_sampler_instance.x_maximum),
            y_bounds=(self.collocation_sampler_instance.y_minimum, self.collocation_sampler_instance.y_maximum)
        )
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
        
        self.curriculum_training_manager_instance.train_source_ramping(
            stages=stages,
            epochs_per_stage=epochs_per_stage,
            points_tensor=points_tensor
        )
        # Khôi phục trạng thái mạng tốt nhất sau khi kết thúc huấn luyện
        if self.training_manager_instance.best_model_state is not None:
            self.pinn_architecture_instance.load_state_dict(self.training_manager_instance.best_model_state)

    def evaluate_diagnostics(self, number_of_points=10000):
        # 1. Tính toán Residual RMS và Max trên lưới ngẫu nhiên Sobol
        bulk_points = self.collocation_sampler_instance.generate_uniform_points_tensor(number_of_points)
        
        phys_props = self.geometry_engine_instance.evaluate_global_physical_properties(bulk_points)
        nu = phys_props["reluctivity"]
        J_z = phys_props["current_density_z"]
        H_cx = phys_props["coercive_field_x"]
        H_cy = phys_props["coercive_field_y"]

        A_z_star = self.pinn_architecture_instance(bulk_points)
        residual_star = self.maxwell_pde_loss_instance.compute_residual(
            xy=bulk_points, A_z_star=A_z_star, nu=nu, J_z=J_z, H_cx=H_cx, H_cy=H_cy
        )
        
        r_rms = torch.sqrt(torch.mean(residual_star**2)).item()
        r_max = torch.max(torch.abs(residual_star)).item()
        
        # 2. Tính toán sai số tại biên (E_boundary = max |A_z| trên 4 cạnh)
        x_min = self.collocation_sampler_instance.x_minimum
        x_max = self.collocation_sampler_instance.x_maximum
        y_min = self.collocation_sampler_instance.y_minimum
        y_max = self.collocation_sampler_instance.y_maximum
        
        num_b_points = 1000
        b_points_top = torch.cat([torch.empty(num_b_points, 1).uniform_(x_min, x_max), torch.full((num_b_points, 1), y_max)], dim=1)
        b_points_bottom = torch.cat([torch.empty(num_b_points, 1).uniform_(x_min, x_max), torch.full((num_b_points, 1), y_min)], dim=1)
        b_points_left = torch.cat([torch.full((num_b_points, 1), x_min), torch.empty(num_b_points, 1).uniform_(y_min, y_max)], dim=1)
        b_points_right = torch.cat([torch.full((num_b_points, 1), x_max), torch.empty(num_b_points, 1).uniform_(y_min, y_max)], dim=1)
        
        boundary_points = torch.cat([b_points_top, b_points_bottom, b_points_left, b_points_right], dim=0)
        
        with torch.no_grad():
            A_z_boundary_star = self.pinn_architecture_instance(boundary_points)
            A_z_boundary_phys = A_z_boundary_star * self.A0
        
        e_boundary = torch.max(torch.abs(A_z_boundary_phys)).item()
        
        return {
            "R_RMS": r_rms,
            "R_max": r_max,
            "E_boundary": e_boundary
        }

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

    # 3. Cập nhật Test: Chạy và in chẩn đoán trước khi vẽ biểu đồ
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

    with open(training_manager_path, 'w', encoding='utf-8') as f: f.write(training_manager_source_code)
    with open(electro_magnetic_path, 'w', encoding='utf-8') as f: f.write(electro_magnetic_source_code)
    with open(test_path, 'w', encoding='utf-8') as f: f.write(test_source_code)
        
    print("Hoàn tất Kịch bản 3: Tích hợp Diagnostics tự động và hệ thống lưu trữ Model Checkpoint!")

if __name__ == '__main__':
    execute_scenario_3_diagnostics_and_checkpointing()