import torch
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
