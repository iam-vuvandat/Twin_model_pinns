import os

def execute_step_4():
    base_directory = os.path.dirname(os.path.abspath(__file__))
    project_root_directory = os.path.abspath(os.path.join(base_directory, '..'))
    
    target_file_path = os.path.join(project_root_directory, 'electro_magnetic_pinn.py')
    
    new_code = """import torch
import torch.nn as nn
from pinn_architecture import PINNArchitecture
from training_manager import TrainingManager
from physics_domain.physical_equations.maxwell_pde_loss import MaxwellPDELoss

class ElectroMagneticPINN:
    # Mở rộng __init__ để hỗ trợ tham số Fourier
    def __init__(self, geometry_engine_instance, collocation_sampler_instance, hidden_layers=4, hidden_neurons=64, activation_function=nn.SiLU(), use_fourier=True, fourier_features=64, fourier_scale=1.0):
        self.geometry_engine_instance = geometry_engine_instance
        self.collocation_sampler_instance = collocation_sampler_instance
        
        self.L0 = self.collocation_sampler_instance.x_maximum
        self.H0 = 800000.0
        self.nu0 = self.geometry_engine_instance.vacuum_reluctivity
        self.A0 = (self.H0 * self.L0) / self.nu0
        
        # Khởi tạo kiến trúc 4 nhánh với Fourier
        self.pinn_architecture_instance = PINNArchitecture(
            domain_scale=self.L0,
            hidden_layers=hidden_layers,
            hidden_neurons=hidden_neurons,
            activation_function=activation_function,
            use_fourier=use_fourier,
            fourier_features=fourier_features,
            fourier_scale=fourier_scale
        )
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
        
        # Trích xuất masks_dict từ từ điển vật lý
        masks_dict = physical_properties_dictionary.get("masks_dict", None)
        
        print(f"--- Standard Adam Training ({epochs_adam} Epochs) ---")
        self.training_manager_instance.train_adam(
            epochs=epochs_adam,
            points_tensor=points_tensor,
            reluctivity_tensor=physical_properties_dictionary["reluctivity"],
            current_density_z_tensor=physical_properties_dictionary["current_density_z"],
            coercive_field_x_tensor=physical_properties_dictionary["coercive_field_x"],
            coercive_field_y_tensor=physical_properties_dictionary["coercive_field_y"],
            masks_dict=masks_dict  # Bổ sung truyền mask
        )
        
        print(f"--- L-BFGS Refinement ({epochs_lbfgs} Epochs) ---")
        self.training_manager_instance.train_lbfgs(
            epochs=epochs_lbfgs, 
            points_tensor=points_tensor, 
            reluctivity_tensor=physical_properties_dictionary["reluctivity"], 
            current_density_z_tensor=physical_properties_dictionary["current_density_z"], 
            coercive_field_x_tensor=physical_properties_dictionary["coercive_field_x"], 
            coercive_field_y_tensor=physical_properties_dictionary["coercive_field_y"],
            masks_dict=masks_dict  # Bổ sung truyền mask
        )

    def predict_magnetic_vector_potential(self, points_tensor):
        self.pinn_architecture_instance.eval()
        with torch.no_grad():
            # Phải tính mask trước khi dự đoán
            physical_props = self.geometry_engine_instance.evaluate_global_physical_properties(points_tensor)
            masks_dict = physical_props.get("masks_dict", None)
            A_z_star = self.pinn_architecture_instance(points_tensor, masks_dict)
        return A_z_star * self.A0

    def evaluate_fields(self, points_tensor):
        self.pinn_architecture_instance.eval()
        points_tensor.requires_grad_(True)
        
        # Phải tính mask trước khi tính các trường
        with torch.no_grad():
            physical_props = self.geometry_engine_instance.evaluate_global_physical_properties(points_tensor)
            masks_dict = physical_props.get("masks_dict", None)
            
        A_z_star = self.pinn_architecture_instance(points_tensor, masks_dict)
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
    
    with open(target_file_path, 'w', encoding='utf-8') as f:
        f.write(new_code)
        
    print(f"BƯỚC 4 HOÀN TẤT: Đã cập nhật thành công tệp:\n{target_file_path}")
    print("Quản lý luồng (ElectroMagneticPINN) đã tích hợp thành công masks_dict vào quá trình huấn luyện và đánh giá.")

if __name__ == "__main__":
    execute_step_4()