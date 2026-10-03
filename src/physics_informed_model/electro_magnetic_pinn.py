import torch
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
