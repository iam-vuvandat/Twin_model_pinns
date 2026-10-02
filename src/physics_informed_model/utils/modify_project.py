import os

def fix_all_signatures():
    base_directory = os.path.dirname(os.path.abspath(__file__))
    project_root_directory = os.path.abspath(os.path.join(base_directory, '..'))
    
    curriculum_path = os.path.join(project_root_directory, 'curriculum_training_manager.py')
    pinn_path = os.path.join(project_root_directory, 'electro_magnetic_pinn.py')

    curriculum_source_code = """import torch
from training_manager import TrainingManager

class CurriculumTrainingManager:
    def __init__(self, training_manager_instance: TrainingManager):
        self.training_manager_instance = training_manager_instance

    def train_source_ramping(self, stages, epochs_per_stage, points_tensor, reluctivity_tensor, current_density_z_tensor, coercive_field_x_tensor, coercive_field_y_tensor):
        for stage in range(1, stages + 1):
            alpha = stage / stages
            
            current_density_z_tensor_scaled = current_density_z_tensor * alpha
            coercive_field_x_tensor_scaled = coercive_field_x_tensor * alpha
            coercive_field_y_tensor_scaled = coercive_field_y_tensor * alpha
            
            print(f"--- Curriculum Stage {stage}/{stages} (Alpha = {alpha:.2f}) ---")
            
            self.training_manager_instance.train_adam(
                epochs=epochs_per_stage,
                points_tensor=points_tensor,
                reluctivity_tensor=reluctivity_tensor,
                current_density_z_tensor=current_density_z_tensor_scaled,
                coercive_field_x_tensor=coercive_field_x_tensor_scaled,
                coercive_field_y_tensor=coercive_field_y_tensor_scaled
            )
            
        print("--- Curriculum L-BFGS Refinement (Alpha = 1.00) ---")
        
        self.training_manager_instance.train_lbfgs(
            epochs=100, 
            points_tensor=points_tensor, 
            reluctivity_tensor=reluctivity_tensor, 
            current_density_z_tensor=current_density_z_tensor, 
            coercive_field_x_tensor=coercive_field_x_tensor, 
            coercive_field_y_tensor=coercive_field_y_tensor
        )
"""

    pinn_source_code = """import torch
from pinn_architecture import PINNArchitecture
from training_manager import TrainingManager
from curriculum_training_manager import CurriculumTrainingManager
from physics_domain.physical_equations.maxwell_pde_loss import MaxwellPDELoss

class ElectroMagneticPINN:
    def __init__(self, geometry_engine_instance, collocation_sampler_instance):
        self.geometry_engine_instance = geometry_engine_instance
        self.collocation_sampler_instance = collocation_sampler_instance
        
        self.pinn_architecture_instance = PINNArchitecture(domain_scale=self.collocation_sampler_instance.x_maximum)
        self.maxwell_pde_loss_instance = MaxwellPDELoss()
        
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
            magnetic_vector_potential_z_tensor = self.pinn_architecture_instance(points_tensor)
        return magnetic_vector_potential_z_tensor

    def evaluate_fields(self, points_tensor):
        self.pinn_architecture_instance.eval()
        points_tensor.requires_grad_(True)
        
        A_z = self.pinn_architecture_instance(points_tensor)
        
        grad_A = torch.autograd.grad(
            outputs=A_z,
            inputs=points_tensor,
            grad_outputs=torch.ones_like(A_z),
            create_graph=False,
            retain_graph=False
        )[0]
        
        B_x = grad_A[:, 1:2]
        B_y = -grad_A[:, 0:1]
        
        return A_z.detach(), B_x.detach(), B_y.detach()
"""

    with open(curriculum_path, 'w', encoding='utf-8') as f:
        f.write(curriculum_source_code)
    with open(pinn_path, 'w', encoding='utf-8') as f:
        f.write(pinn_source_code)
        
    print("Đã loại bỏ hoàn toàn tham số signed_distance_field_tensor khỏi chuỗi Curriculum!")

if __name__ == '__main__':
    fix_all_signatures()