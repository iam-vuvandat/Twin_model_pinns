import torch
from pinn_architecture import PINNArchitecture
from training_manager import TrainingManager
from curriculum_training_manager import CurriculumTrainingManager
from physics_domain.physical_equations.maxwell_pde_loss import MaxwellPDELoss

class ElectroMagneticPINN:
    def __init__(self, geometry_engine_instance, collocation_sampler_instance):
        self.geometry_engine_instance = geometry_engine_instance
        self.collocation_sampler_instance = collocation_sampler_instance
        
        self.pinn_architecture_instance = PINNArchitecture()
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
        
        signed_distance_field_tensor = self.geometry_engine_instance.compute_global_signed_distance_field(points_tensor)
        physical_properties_dictionary = self.geometry_engine_instance.evaluate_global_physical_properties(points_tensor)
        
        self.curriculum_training_manager_instance.train_source_ramping(
            stages=stages,
            epochs_per_stage=epochs_per_stage,
            points_tensor=points_tensor,
            signed_distance_field_tensor=signed_distance_field_tensor,
            reluctivity_tensor=physical_properties_dictionary["reluctivity"],
            current_density_z_tensor=physical_properties_dictionary["current_density_z"],
            coercive_field_x_tensor=physical_properties_dictionary["coercive_field_x"],
            coercive_field_y_tensor=physical_properties_dictionary["coercive_field_y"]
        )

    def predict_magnetic_vector_potential(self, points_tensor):
        self.pinn_architecture_instance.eval()
        signed_distance_field_tensor = self.geometry_engine_instance.compute_global_signed_distance_field(points_tensor)
        
        with torch.no_grad():
            magnetic_vector_potential_z_tensor = self.pinn_architecture_instance(points_tensor, signed_distance_field_tensor)
            
        return magnetic_vector_potential_z_tensor
