import torch
from .training_manager import TrainingManager

class CurriculumTrainingManager:
    def __init__(self, training_manager: TrainingManager):
        self.training_manager = training_manager

    def train_source_ramping(self, stages, epochs_per_stage, xy, sdf_boundary, iron_mask, magnet_mask, slot_masks_dict, slot_current_dict, H_cx, H_cy):
        for stage in range(1, stages + 1):
            alpha = stage / stages
            
            current_dict_scaled = {k: v * alpha for k, v in slot_current_dict.items()}
            H_cx_scaled = H_cx * alpha
            H_cy_scaled = H_cy * alpha
            
            print(f"--- Curriculum Stage {stage}/{stages} (Alpha = {alpha:.2f}) ---")
            
            self.training_manager.train_adam(
                epochs_per_stage, xy, sdf_boundary, iron_mask, magnet_mask, 
                slot_masks_dict, current_dict_scaled, H_cx_scaled, H_cy_scaled
            )
            
        print("--- Curriculum L-BFGS Refinement (Alpha = 1.00) ---")
        
        self.training_manager.train_lbfgs(
            epochs=100, 
            xy=xy, 
            sdf_boundary=sdf_boundary, 
            iron_mask=iron_mask, 
            magnet_mask=magnet_mask, 
            slot_masks_dict=slot_masks_dict, 
            slot_current_dict=slot_current_dict, 
            H_cx=H_cx, 
            H_cy=H_cy
        )