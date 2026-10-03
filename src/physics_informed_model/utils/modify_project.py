import os
import subprocess

def patch_and_push_project():
    base_directory = os.path.dirname(os.path.abspath(__file__))
    project_root_directory = os.path.abspath(os.path.join(base_directory, '..'))
    
    electro_magnetic_path = os.path.join(project_root_directory, 'electro_magnetic_pinn.py')
    
    # Nội dung chuẩn 100% của electro_magnetic_pinn.py (Đã gỡ bỏ hoàn toàn Curriculum, khớp với test_simulation.py)
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

    # Ghi đè file electro_magnetic_pinn.py
    with open(electro_magnetic_path, 'w', encoding='utf-8') as f:
        f.write(electro_magnetic_code)
    print("Đã vá xong tệp electro_magnetic_pinn.py!")

    # Tự động đẩy code lên GitHub để Colab nhận diện bản cập nhật mới nhất
    print("Đang đồng bộ code lên GitHub...")
    try:
        subprocess.run(["git", "add", "."], check=True, cwd=project_root_directory)
        subprocess.run(["git", "commit", "-m", "Patch electro_magnetic_pinn.py to match test_simulation.py arguments"], check=True, cwd=project_root_directory)
        subprocess.run(["git", "push", "origin", "main"], check=True, cwd=project_root_directory)
        print(">> ĐỒNG BỘ GITHUB THÀNH CÔNG! Bây giờ bạn có thể chạy lại trên Colab.")
    except Exception as e:
        print(">> Lỗi khi đẩy Git:", e)

if __name__ == '__main__':
    patch_and_push_project()