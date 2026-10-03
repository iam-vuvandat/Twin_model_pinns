import os

def execute_scenario_2_sampling_and_boundary():
    base_directory = os.path.dirname(os.path.abspath(__file__))
    project_root_directory = os.path.abspath(os.path.join(base_directory, '..'))
    
    collocation_path = os.path.join(project_root_directory, 'physics_domain', 'collocation_sampler.py')
    pinn_path = os.path.join(project_root_directory, 'pinn_architecture.py')
    electro_magnetic_path = os.path.join(project_root_directory, 'electro_magnetic_pinn.py')

    # 1. Nâng cấp CollocationSampler: Tích hợp Sobol và max_attempts
    collocation_source_code = """import torch

class CollocationSampler:
    def __init__(self, x_boundaries_tuple, y_boundaries_tuple):
        self.x_minimum = x_boundaries_tuple[0]
        self.x_maximum = x_boundaries_tuple[1]
        self.y_minimum = y_boundaries_tuple[0]
        self.y_maximum = y_boundaries_tuple[1]
        # Khởi tạo engine tạo số giả ngẫu nhiên phân bố đều (Sobol)
        self.sobol_engine = torch.quasirandom.SobolEngine(dimension=2, scramble=True)

    def generate_uniform_points_tensor(self, number_of_points):
        sobol_points = self.sobol_engine.draw(number_of_points)
        points_tensor = torch.zeros_like(sobol_points, dtype=torch.float32)
        points_tensor[:, 0] = sobol_points[:, 0] * (self.x_maximum - self.x_minimum) + self.x_minimum
        points_tensor[:, 1] = sobol_points[:, 1] * (self.y_maximum - self.y_minimum) + self.y_minimum
        points_tensor.requires_grad_(True)
        return points_tensor

    def generate_interface_points_tensor(self, geometry_object, number_of_points, distance_threshold, max_attempts=50):
        collected_points = []
        collected_count = 0
        pool_size_value = number_of_points * 20
        attempts = 0
        
        while collected_count < number_of_points and attempts < max_attempts:
            attempts += 1
            sobol_pool = self.sobol_engine.draw(pool_size_value)
            points_pool_tensor = torch.zeros_like(sobol_pool, dtype=torch.float32)
            points_pool_tensor[:, 0] = sobol_pool[:, 0] * (self.x_maximum - self.x_minimum) + self.x_minimum
            points_pool_tensor[:, 1] = sobol_pool[:, 1] * (self.y_maximum - self.y_minimum) + self.y_minimum
            
            signed_distance_field_tensor = geometry_object.compute_global_signed_distance_field(points_pool_tensor)
            mask_tensor = torch.abs(signed_distance_field_tensor) < distance_threshold
            mask_1d = mask_tensor.squeeze()
            
            if mask_1d.any():
                valid_points = points_pool_tensor[mask_1d]
                collected_points.append(valid_points)
                collected_count += valid_points.shape[0]
                
        if attempts == max_attempts and collected_count < number_of_points:
            print(f"[CẢNH BÁO] Lấy mẫu Interface đạt max_attempts ({max_attempts}). Chỉ thu được {collected_count}/{number_of_points} điểm.")
            
        if collected_count == 0:
            return self.generate_uniform_points_tensor(number_of_points)

        interface_points_tensor = torch.cat(collected_points, dim=0)[:number_of_points, :]
        interface_points_tensor = interface_points_tensor.detach().clone()
        interface_points_tensor.requires_grad_(True)
        return interface_points_tensor

    def generate_combined_points_tensor(self, geometry_object, number_of_uniform_points, number_of_interface_points, distance_threshold):
        uniform_points_tensor = self.generate_uniform_points_tensor(number_of_uniform_points)
        interface_points_tensor = self.generate_interface_points_tensor(geometry_object, number_of_interface_points, distance_threshold)
        
        combined_points_tensor = torch.cat([uniform_points_tensor, interface_points_tensor], dim=0)
        combined_points_tensor = combined_points_tensor.detach().clone()
        combined_points_tensor.requires_grad_(True)
        return combined_points_tensor
"""

    # 2. Cập nhật PINN Architecture: Tổng quát hóa Hard Boundary cho hình chữ nhật bất kỳ
    pinn_architecture_source_code = """import torch
import torch.nn as nn

class PINNArchitecture(nn.Module):
    def __init__(self, input_dim=2, hidden_layers=4, hidden_neurons=50, output_dim=1, x_bounds=(-0.05, 0.05), y_bounds=(-0.05, 0.05)):
        super().__init__()
        self.x_min, self.x_max = x_bounds
        self.y_min, self.y_max = y_bounds
        
        layers = []
        layers.append(nn.Linear(input_dim, hidden_neurons))
        layers.append(nn.Tanh())
        
        for _ in range(hidden_layers - 1):
            layers.append(nn.Linear(hidden_neurons, hidden_neurons))
            layers.append(nn.Tanh())
            
        layers.append(nn.Linear(hidden_neurons, output_dim))
        
        self.network = nn.Sequential(*layers)
        self._initialize_weights()

    def _initialize_weights(self):
        for module in self.network:
            if isinstance(module, nn.Linear):
                nn.init.xavier_normal_(module.weight)
                nn.init.zeros_(module.bias)

    def boundary_factor(self, xy):
        # Chuyển đổi tọa độ thành xi, eta trong khoảng [-1, 1]
        xi = (2.0 * xy[:, 0:1] - (self.x_max + self.x_min)) / (self.x_max - self.x_min)
        eta = (2.0 * xy[:, 1:2] - (self.y_max + self.y_min)) / (self.y_max - self.y_min)
        
        x_factor = 1.0 - xi**2
        y_factor = 1.0 - eta**2
        return x_factor * y_factor

    def forward(self, xy):
        # Chuẩn hóa đầu vào của mạng Nơ-ron về [-1, 1]
        xi = (2.0 * xy[:, 0:1] - (self.x_max + self.x_min)) / (self.x_max - self.x_min)
        eta = (2.0 * xy[:, 1:2] - (self.y_max + self.y_min)) / (self.y_max - self.y_min)
        xy_normalized = torch.cat([xi, eta], dim=1)
        
        raw_output = self.network(xy_normalized)
        
        A_z_star = raw_output * self.boundary_factor(xy)
        return A_z_star
"""

    # 3. Cập nhật ElectroMagneticPINN để truyền tuple boundary vào mạng nơ-ron thay vì scale tĩnh
    electro_magnetic_source_code = """import torch
from pinn_architecture import PINNArchitecture
from training_manager import TrainingManager
from curriculum_training_manager import CurriculumTrainingManager
from physics_domain.physical_equations.maxwell_pde_loss import MaxwellPDELoss

class ElectroMagneticPINN:
    def __init__(self, geometry_engine_instance, collocation_sampler_instance):
        self.geometry_engine_instance = geometry_engine_instance
        self.collocation_sampler_instance = collocation_sampler_instance
        
        # Tham chiếu dựa trên kích thước miền lấy mẫu lớn nhất
        self.L0 = max(abs(self.collocation_sampler_instance.x_maximum), abs(self.collocation_sampler_instance.x_minimum))
        self.H0 = 800000.0
        self.nu0 = self.geometry_engine_instance.vacuum_reluctivity
        self.A0 = (self.H0 * self.L0) / self.nu0
        
        # [CẬP NHẬT] Truyền trực tiếp giới hạn không gian để tính biên tổng quát
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

    with open(collocation_path, 'w', encoding='utf-8') as f: f.write(collocation_source_code)
    with open(pinn_path, 'w', encoding='utf-8') as f: f.write(pinn_architecture_source_code)
    with open(electro_magnetic_path, 'w', encoding='utf-8') as f: f.write(electro_magnetic_source_code)
        
    print("Hoàn tất Kịch bản 2: Tích hợp Sobol Sampling và Generalized Hard Boundary!")

if __name__ == '__main__':
    execute_scenario_2_sampling_and_boundary()