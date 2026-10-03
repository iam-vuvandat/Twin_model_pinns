import os

def apply_nondimensionalization_and_tanh():
    base_directory = os.path.dirname(os.path.abspath(__file__))
    project_root_directory = os.path.abspath(os.path.join(base_directory, '..'))
    
    pinn_architecture_path = os.path.join(project_root_directory, 'pinn_architecture.py')
    maxwell_loss_path = os.path.join(project_root_directory, 'physics_domain', 'physical_equations', 'maxwell_pde_loss.py')
    training_manager_path = os.path.join(project_root_directory, 'training_manager.py')
    electro_magnetic_pinn_path = os.path.join(project_root_directory, 'electro_magnetic_pinn.py')

    # 1. Cập nhật PINN Architecture: Dùng nn.Tanh() thay vì nn.SiLU()
    pinn_architecture_source_code = """import torch
import torch.nn as nn

class PINNArchitecture(nn.Module):
    def __init__(self, input_dim=2, hidden_layers=4, hidden_neurons=50, output_dim=1, domain_scale=0.05):
        super().__init__()
        self.domain_scale = domain_scale
        
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
        x_factor = 1.0 - (xy[:, 0:1] / self.domain_scale)**2
        y_factor = 1.0 - (xy[:, 1:2] / self.domain_scale)**2
        return x_factor * y_factor

    def forward(self, xy):
        xy_normalized = xy / self.domain_scale
        raw_output = self.network(xy_normalized)
        
        A_z_star = raw_output * self.boundary_factor(xy)
        return A_z_star
"""

    # 2. Cập nhật phương trình Maxwell thành Non-dimensional PDE
    maxwell_loss_source_code = """import torch

class MaxwellPDELoss:
    def __init__(self, L0=0.05, H0=800000.0, nu0=795774.715459):
        # Các hằng số tham chiếu để chuẩn hóa (Non-dimensionalization constants)
        self.L0 = L0
        self.H0 = H0
        self.nu0 = nu0

    def compute_residual(self, xy, A_z_star, nu, J_z, H_cx, H_cy):
        # 1. Biến đổi đại lượng vật lý thành đại lượng không thứ nguyên (Dimensionless variables)
        nu_star = nu / self.nu0
        H_cx_star = H_cx / self.H0
        H_cy_star = H_cy / self.H0
        # Mật độ dòng J = curl(H) -> J_0 = H_0 / L_0
        J_z_star = J_z / (self.H0 / self.L0)
        
        # 2. Lấy đạo hàm của A_z_star theo x, y (lưu ý xy là tọa độ vật lý)
        grad_A_star = torch.autograd.grad(
            outputs=A_z_star,
            inputs=xy,
            grad_outputs=torch.ones_like(A_z_star),
            create_graph=True,
            retain_graph=True
        )[0]
        
        # Chuyển đổi vi phân: d/dx = (1/L0) * d/dx_star -> d/dx_star = d/dx * L0
        dAz_star_dx_star = grad_A_star[:, 0:1] * self.L0
        dAz_star_dy_star = grad_A_star[:, 1:2] * self.L0
        
        # 3. Tính từ trường không thứ nguyên
        H_x_star = nu_star * dAz_star_dy_star - H_cx_star
        H_y_star = -nu_star * dAz_star_dx_star - H_cy_star
        
        # 4. Lấy đạo hàm của H_star theo x, y vật lý
        grad_Hx_star = torch.autograd.grad(
            outputs=H_x_star,
            inputs=xy,
            grad_outputs=torch.ones_like(H_x_star),
            create_graph=True,
            retain_graph=True
        )[0]
        dHx_star_dy_star = grad_Hx_star[:, 1:2] * self.L0
        
        grad_Hy_star = torch.autograd.grad(
            outputs=H_y_star,
            inputs=xy,
            grad_outputs=torch.ones_like(H_y_star),
            create_graph=True,
            retain_graph=True
        )[0]
        dHy_star_dx_star = grad_Hy_star[:, 0:1] * self.L0
        
        # 5. Phương trình dư không thứ nguyên (Dimensionless Residual) sẽ mang biên độ ~1
        residual_star = dHy_star_dx_star - dHx_star_dy_star - J_z_star
        return residual_star
"""

    # 3. Loại bỏ Loss Scaling Factor khỏi TrainingManager
    training_manager_source_code = """import torch
import torch.optim as optim

class TrainingManager:
    # [CẬP NHẬT]: Đã gỡ bỏ loss_scaling_factor vì hệ thống đã tự cân bằng vật lý
    def __init__(self, model, pde_evaluator, lr_adam=1e-3):
        self.model = model
        self.pde_evaluator = pde_evaluator
        
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

    def compute_loss(self, points_tensor, reluctivity_tensor, current_density_z_tensor, coercive_field_x_tensor, coercive_field_y_tensor):
        A_z_star = self.model(points_tensor)
        
        residual_star = self.pde_evaluator.compute_residual(
            xy=points_tensor,
            A_z_star=A_z_star,
            nu=reluctivity_tensor,
            J_z=current_density_z_tensor,
            H_cx=coercive_field_x_tensor,
            H_cy=coercive_field_y_tensor
        )
        
        # Loss tính toán trực tiếp trên phần dư chuẩn hóa
        loss_pde = torch.mean(residual_star**2)
        return loss_pde

    def train_adam(self, epochs, points_tensor, reluctivity_tensor, current_density_z_tensor, coercive_field_x_tensor, coercive_field_y_tensor):
        self.model.train()
        best_loss = float('inf')
        best_model_state = {key: value.cpu().clone() for key, value in self.model.state_dict().items()}
        
        scheduler_adam = optim.lr_scheduler.CosineAnnealingLR(self.optimizer_adam, T_max=epochs, eta_min=1e-6)
        
        for epoch in range(epochs):
            self.optimizer_adam.zero_grad()
            
            loss = self.compute_loss(
                points_tensor, reluctivity_tensor, 
                current_density_z_tensor, coercive_field_x_tensor, coercive_field_y_tensor
            )
            
            if torch.isnan(loss) or loss.item() > 1.5 * best_loss:
                self.model.load_state_dict(best_model_state)
                for param_group in self.optimizer_adam.param_groups:
                    param_group['lr'] *= 0.8
                continue
                
            loss.backward(retain_graph=True)
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

    def train_lbfgs(self, epochs, points_tensor, reluctivity_tensor, current_density_z_tensor, coercive_field_x_tensor, coercive_field_y_tensor):
        self.model.train()
        for epoch in range(epochs):
            def closure():
                self.optimizer_lbfgs.zero_grad()
                loss = self.compute_loss(
                    points_tensor, reluctivity_tensor, 
                    current_density_z_tensor, coercive_field_x_tensor, coercive_field_y_tensor
                )
                loss.backward(retain_graph=True)
                return loss
            
            loss_val = self.optimizer_lbfgs.step(closure)
            print(f"L-BFGS Epoch {epoch + 1}: Loss = {loss_val.item():.6e}")
"""

    # 4. Quản lý hằng số và khôi phục giá trị vật lý khi vẽ đồ thị
    electro_magnetic_pinn_source_code = """import torch
from pinn_architecture import PINNArchitecture
from training_manager import TrainingManager
from curriculum_training_manager import CurriculumTrainingManager
from physics_domain.physical_equations.maxwell_pde_loss import MaxwellPDELoss

class ElectroMagneticPINN:
    def __init__(self, geometry_engine_instance, collocation_sampler_instance):
        self.geometry_engine_instance = geometry_engine_instance
        self.collocation_sampler_instance = collocation_sampler_instance
        
        # Khởi tạo các hệ số chuẩn hóa (Non-dimensionalization scaling factors)
        self.L0 = self.collocation_sampler_instance.x_maximum
        self.H0 = 800000.0
        self.nu0 = self.geometry_engine_instance.vacuum_reluctivity
        # Hằng số chuẩn hóa hệ quả cho Từ thế vector
        self.A0 = (self.H0 * self.L0) / self.nu0
        
        self.pinn_architecture_instance = PINNArchitecture(domain_scale=self.L0)
        self.maxwell_pde_loss_instance = MaxwellPDELoss(L0=self.L0, H0=self.H0, nu0=self.nu0)
        
        self.training_manager_instance = TrainingManager(
            model=self.pinn_architecture_instance,
            pde_evaluator=self.maxwell_pde_loss_instance
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
        
        physical_properties_dictionary = self.geometry_engine_instance.evaluate_global_physical_properties(points_tensor)
        
        self.curriculum_training_manager_instance.train_source_ramping(
            stages=stages,
            epochs_per_stage=epochs_per_stage,
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
        # Trả về giá trị vật lý thực tế: A_phys = A_star * A_0
        return A_z_star * self.A0

    def evaluate_fields(self, points_tensor):
        self.pinn_architecture_instance.eval()
        points_tensor.requires_grad_(True)
        
        A_z_star = self.pinn_architecture_instance(points_tensor)
        
        # Khôi phục A_z về đơn vị vật lý trước khi lấy đạo hàm B
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

    with open(pinn_architecture_path, 'w', encoding='utf-8') as f: f.write(pinn_architecture_source_code)
    with open(maxwell_loss_path, 'w', encoding='utf-8') as f: f.write(maxwell_loss_source_code)
    with open(training_manager_path, 'w', encoding='utf-8') as f: f.write(training_manager_source_code)
    with open(electro_magnetic_pinn_path, 'w', encoding='utf-8') as f: f.write(electro_magnetic_pinn_source_code)
        
    print("Đã hoàn tất cấu trúc mạng Tanh và chuẩn hóa không thứ nguyên (Non-dimensionalization)!")

if __name__ == '__main__':
    apply_nondimensionalization_and_tanh()