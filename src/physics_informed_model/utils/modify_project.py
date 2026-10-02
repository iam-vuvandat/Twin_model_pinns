import os

def fix_curriculum_training_manager():
    base_directory = os.path.dirname(os.path.abspath(__file__))
    project_root_directory = os.path.abspath(os.path.join(base_directory, '..'))
    
    curriculum_path = os.path.join(project_root_directory, 'curriculum_training_manager.py')

    source_code = """import torch
from training_manager import TrainingManager

class CurriculumTrainingManager:
    def __init__(self, training_manager_instance: TrainingManager):
        self.training_manager_instance = training_manager_instance

    def train_source_ramping(self, stages, epochs_per_stage, points_tensor, signed_distance_field_tensor, reluctivity_tensor, current_density_z_tensor, coercive_field_x_tensor, coercive_field_y_tensor):
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

    with open(curriculum_path, 'w', encoding='utf-8') as f:
        f.write(source_code)
        
    print("Đã cập nhật lại curriculum_training_manager.py thành công!")

if __name__ == '__main__':
    fix_curriculum_training_manager()