import os
import shutil

def modify_project_structure():
    base_directory = os.path.dirname(os.path.abspath(__file__))
    project_root_directory = os.path.abspath(os.path.join(base_directory, '..'))
    
    geometry_engine_directory = os.path.join(project_root_directory, 'geometry_engine')
    segment_directory = os.path.join(geometry_engine_directory, 'segment')
    templates_directory = os.path.join(geometry_engine_directory, 'templates')
    physics_domain_directory = os.path.join(project_root_directory, 'physics_domain')
    physical_equations_directory = os.path.join(physics_domain_directory, 'physical_equations')
    materials_directory = os.path.join(physics_domain_directory, 'materials')
    
    if os.path.exists(materials_directory):
        shutil.rmtree(materials_directory)
    if os.path.exists(templates_directory):
        shutil.rmtree(templates_directory)
        
    obsolete_files = [
        os.path.join(physics_domain_directory, 'collocation_sampling.py'),
        os.path.join(project_root_directory, 'physics_neural_network.py'),
        os.path.join(project_root_directory, 'trial_function_wrapper.py')
    ]
    for obs_file in obsolete_files:
        if os.path.exists(obs_file):
            os.remove(obs_file)

    os.makedirs(geometry_engine_directory, exist_ok=True)
    os.makedirs(segment_directory, exist_ok=True)
    os.makedirs(physics_domain_directory, exist_ok=True)
    os.makedirs(physical_equations_directory, exist_ok=True)

    segment_init_file_path = os.path.join(segment_directory, '__init__.py')
    segment_file_path = os.path.join(segment_directory, 'segment.py')
    polygon_sdf_file_path = os.path.join(segment_directory, 'polygon_signed_distance_field.py')
    
    global_sdf_file_path = os.path.join(geometry_engine_directory, 'global_signed_distance_field.py')
    global_properties_file_path = os.path.join(geometry_engine_directory, 'global_physical_properties_evaluation.py')
    geometry_file_path = os.path.join(geometry_engine_directory, 'geometry.py')
    
    collocation_sampler_file_path = os.path.join(physics_domain_directory, 'collocation_sampler.py')
    maxwell_pde_loss_file_path = os.path.join(physical_equations_directory, 'maxwell_pde_loss.py')
    
    electro_magnetic_pinn_file_path = os.path.join(project_root_directory, 'electro_magnetic_pinn.py')
    pinn_architecture_file_path = os.path.join(project_root_directory, 'pinn_architecture.py')
    training_manager_file_path = os.path.join(project_root_directory, 'training_manager.py')
    curriculum_training_manager_file_path = os.path.join(project_root_directory, 'curriculum_training_manager.py')
    test_simulation_file_path = os.path.join(project_root_directory, 'test_simulation.py')

    init_source_code = ""

    polygon_sdf_source_code = """import torch

def compute_polygon_signed_distance_field(vertices_tensor, points_tensor):
    if vertices_tensor is None:
        raise ValueError("Segment vertices must be set before computing signed distance field.")
        
    computation_device = points_tensor.device
    computation_dtype = points_tensor.dtype

    vertices_on_device = vertices_tensor.to(
        device=computation_device,
        dtype=computation_dtype,
    )
    
    start_points = vertices_on_device
    end_points = torch.roll(vertices_on_device, shifts=-1, dims=0)
    
    edge_vectors = end_points - start_points
    point_to_start_vectors = points_tensor.unsqueeze(1) - start_points.unsqueeze(0)
    
    dot_product_point_to_start_and_edge = torch.sum(point_to_start_vectors * edge_vectors.unsqueeze(0), dim=2)
    dot_product_edge_and_edge = torch.sum(edge_vectors * edge_vectors, dim=1).unsqueeze(0)
    
    dot_product_edge_and_edge = torch.clamp(
        dot_product_edge_and_edge,
        min=torch.finfo(computation_dtype).eps,
    )
    
    projection_parameter = dot_product_point_to_start_and_edge / dot_product_edge_and_edge
    clamped_projection_parameter = torch.clamp(projection_parameter, min=0.0, max=1.0)
    
    closest_points = start_points.unsqueeze(0) + clamped_projection_parameter.unsqueeze(-1) * edge_vectors.unsqueeze(0)
    
    diff_vectors = points_tensor.unsqueeze(1) - closest_points
    distances_to_edges = torch.sqrt(torch.sum(diff_vectors * diff_vectors, dim=2) + 1e-12)
    
    minimum_distances, _ = torch.min(distances_to_edges, dim=1)
    
    points_x_coordinates = points_tensor[:, 0].unsqueeze(1)
    points_y_coordinates = points_tensor[:, 1].unsqueeze(1)
    start_points_x_coordinates = start_points[:, 0].unsqueeze(0)
    start_points_y_coordinates = start_points[:, 1].unsqueeze(0)
    end_points_x_coordinates = end_points[:, 0].unsqueeze(0)
    end_points_y_coordinates = end_points[:, 1].unsqueeze(0)
    
    condition_y_between_start_and_end = (start_points_y_coordinates <= points_y_coordinates) & (points_y_coordinates < end_points_y_coordinates)
    condition_y_between_end_and_start = (end_points_y_coordinates <= points_y_coordinates) & (points_y_coordinates < start_points_y_coordinates)
    valid_y_intersection = condition_y_between_start_and_end | condition_y_between_end_and_start
    
    y_difference = end_points_y_coordinates - start_points_y_coordinates
    
    dy_safe = torch.where(
        torch.abs(y_difference) < torch.finfo(computation_dtype).eps,
        torch.full_like(y_difference, 1e-7),
        y_difference,
    )
    
    intersection_x_coordinates = start_points_x_coordinates + (points_y_coordinates - start_points_y_coordinates) * (end_points_x_coordinates - start_points_x_coordinates) / dy_safe
    ray_crossings = valid_y_intersection & (points_x_coordinates < intersection_x_coordinates)
    
    is_point_inside = ray_crossings.sum(dim=1) % 2 == 1
    distance_sign = torch.where(
        is_point_inside,
        -torch.ones_like(minimum_distances),
        torch.ones_like(minimum_distances),
    )
    
    return distance_sign * minimum_distances
"""

    segment_source_code = """import torch
from geometry_engine.segment.polygon_signed_distance_field import compute_polygon_signed_distance_field

class Segment:
    def __init__(self, vertices_list=None):
        self.material_name = "air"
        self.vacuum_reluctivity = 795774.715459
        
        self.relative_permeability = 1.0
        self.reluctivity_function = None
        
        self.coercive_field_x = 0.0
        self.coercive_field_y = 0.0
        self.magnetization_vector_function = None
        
        self.current_density_z_axis = 0.0
        self.current_density_function = None
        
        self.vertices_tensor = None
        if vertices_list is not None:
            self.set_vertices(vertices_list)

    def set_vertices(self, vertices_list):
        self.vertices_tensor = torch.tensor(vertices_list, dtype=torch.float32)
        return self

    def set_material_properties(
        self, 
        name="default", 
        relative_permeability=1.0, 
        reluctivity_function=None,
        coercive_field_x=0.0,
        coercive_field_y=0.0,
        magnetization_vector_function=None, 
        current_density_z_axis=0.0,
        current_density_function=None
    ):
        self.material_name = name
        self.relative_permeability = relative_permeability
        self.reluctivity_function = reluctivity_function
        self.coercive_field_x = coercive_field_x
        self.coercive_field_y = coercive_field_y
        self.magnetization_vector_function = magnetization_vector_function
        self.current_density_z_axis = current_density_z_axis
        self.current_density_function = current_density_function
        return self

    def compute_signed_distance_field(self, points_tensor):
        return compute_polygon_signed_distance_field(self.vertices_tensor, points_tensor)

    def evaluate_reluctivity(self, points_tensor):
        if self.reluctivity_function is not None:
            return self.reluctivity_function(points_tensor)
        constant_reluctivity = self.vacuum_reluctivity / self.relative_permeability
        return torch.full((points_tensor.shape[0], 1), constant_reluctivity, dtype=torch.float32, device=points_tensor.device)

    def evaluate_magnetization_vector(self, points_tensor):
        if self.magnetization_vector_function is not None:
            return self.magnetization_vector_function(points_tensor)
        hx_tensor = torch.full((points_tensor.shape[0], 1), self.coercive_field_x, dtype=torch.float32, device=points_tensor.device)
        hy_tensor = torch.full((points_tensor.shape[0], 1), self.coercive_field_y, dtype=torch.float32, device=points_tensor.device)
        return hx_tensor, hy_tensor

    def evaluate_current_density(self, points_tensor):
        if self.current_density_function is not None:
            return self.current_density_function(points_tensor)
        return torch.full((points_tensor.shape[0], 1), self.current_density_z_axis, dtype=torch.float32, device=points_tensor.device)
"""

    global_sdf_source_code = """import torch

def compute_global_signed_distance_field(segments_list, points_tensor):
    if not segments_list:
        return torch.ones((points_tensor.shape[0], 1), dtype=torch.float32, device=points_tensor.device)
        
    global_signed_distance_field = segments_list[0].compute_signed_distance_field(points_tensor)
    
    for segment_object in segments_list[1:]:
        current_signed_distance_field = segment_object.compute_signed_distance_field(points_tensor)
        global_signed_distance_field = torch.minimum(global_signed_distance_field, current_signed_distance_field)
        
    return global_signed_distance_field
"""

    global_properties_source_code = """import torch

def evaluate_global_physical_properties(segments_list, points_tensor, vacuum_reluctivity):
    number_of_points = points_tensor.shape[0]
    computation_device = points_tensor.device
    
    global_reluctivity_tensor = torch.full((number_of_points, 1), vacuum_reluctivity, dtype=torch.float32, device=computation_device)
    global_coercive_field_x_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)
    global_coercive_field_y_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)
    global_current_density_z_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)
    global_material_classification_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)

    material_index_counter = 1.0

    for segment_object in segments_list:
        signed_distance_field = segment_object.compute_signed_distance_field(points_tensor)
        mask_tensor = signed_distance_field <= 0.0
        mask_1d = mask_tensor.squeeze()
        
        if mask_1d.any():
            points_in_segment = points_tensor[mask_1d]
            
            global_reluctivity_tensor[mask_1d] = segment_object.evaluate_reluctivity(points_in_segment)
            
            hx_tensor, hy_tensor = segment_object.evaluate_magnetization_vector(points_in_segment)
            global_coercive_field_x_tensor[mask_1d] = hx_tensor
            global_coercive_field_y_tensor[mask_1d] = hy_tensor
            
            global_current_density_z_tensor[mask_1d] = segment_object.evaluate_current_density(points_in_segment)
            
            global_material_classification_tensor[mask_1d] = material_index_counter
        
        material_index_counter += 1.0

    return {
        "reluctivity": global_reluctivity_tensor,
        "coercive_field_x": global_coercive_field_x_tensor,
        "coercive_field_y": global_coercive_field_y_tensor,
        "current_density_z": global_current_density_z_tensor,
        "material_classification": global_material_classification_tensor
    }
"""

    geometry_source_code = """import torch
from geometry_engine.segment.segment import Segment
from geometry_engine.global_signed_distance_field import compute_global_signed_distance_field
from geometry_engine.global_physical_properties_evaluation import evaluate_global_physical_properties

class Geometry:
    def __init__(self):
        self.segments_list = []
        self.vacuum_reluctivity = 795774.715459

    def add_segment(self, segment_object):
        self.segments_list.append(segment_object)
        return self

    def compute_global_signed_distance_field(self, points_tensor):
        return compute_global_signed_distance_field(self.segments_list, points_tensor)

    def evaluate_global_physical_properties(self, points_tensor):
        return evaluate_global_physical_properties(self.segments_list, points_tensor, self.vacuum_reluctivity)
"""

    collocation_sampler_source_code = """import torch

class CollocationSampler:
    def __init__(self, x_boundaries_tuple, y_boundaries_tuple):
        self.x_minimum = x_boundaries_tuple[0]
        self.x_maximum = x_boundaries_tuple[1]
        self.y_minimum = y_boundaries_tuple[0]
        self.y_maximum = y_boundaries_tuple[1]

    def generate_uniform_points_tensor(self, number_of_points):
        points_tensor = torch.rand((number_of_points, 2), dtype=torch.float32)
        points_tensor[:, 0] = points_tensor[:, 0] * (self.x_maximum - self.x_minimum) + self.x_minimum
        points_tensor[:, 1] = points_tensor[:, 1] * (self.y_maximum - self.y_minimum) + self.y_minimum
        points_tensor.requires_grad_(True)
        return points_tensor

    def generate_interface_points_tensor(self, geometry_object, number_of_points, distance_threshold):
        collected_points = []
        collected_count = 0
        pool_size_value = number_of_points * 20
        
        while collected_count < number_of_points:
            points_pool_tensor = torch.rand((pool_size_value, 2), dtype=torch.float32)
            points_pool_tensor[:, 0] = points_pool_tensor[:, 0] * (self.x_maximum - self.x_minimum) + self.x_minimum
            points_pool_tensor[:, 1] = points_pool_tensor[:, 1] * (self.y_maximum - self.y_minimum) + self.y_minimum
            
            signed_distance_field_tensor = geometry_object.compute_global_signed_distance_field(points_pool_tensor)
            mask_tensor = torch.abs(signed_distance_field_tensor) < distance_threshold
            mask_1d = mask_tensor.squeeze()
            
            if mask_1d.any():
                valid_points = points_pool_tensor[mask_1d]
                collected_points.append(valid_points)
                collected_count += valid_points.shape[0]
                
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

    maxwell_pde_loss_source_code = """import torch

class MaxwellPDELoss:
    def __init__(self):
        pass

    def compute_residual(self, xy, A_z, nu, J_z, H_cx, H_cy):
        grad_A = torch.autograd.grad(
            outputs=A_z,
            inputs=xy,
            grad_outputs=torch.ones_like(A_z),
            create_graph=True,
            retain_graph=True
        )[0]
        
        dAz_dx = grad_A[:, 0:1]
        dAz_dy = grad_A[:, 1:2]
        
        H_x = nu * dAz_dy - H_cx
        H_y = -nu * dAz_dx - H_cy
        
        grad_Hx = torch.autograd.grad(
            outputs=H_x,
            inputs=xy,
            grad_outputs=torch.ones_like(H_x),
            create_graph=True,
            retain_graph=True
        )[0]
        dHx_dy = grad_Hx[:, 1:2]
        
        grad_Hy = torch.autograd.grad(
            outputs=H_y,
            inputs=xy,
            grad_outputs=torch.ones_like(H_y),
            create_graph=True,
            retain_graph=True
        )[0]
        dHy_dx = grad_Hy[:, 0:1]
        
        residual = dHy_dx - dHx_dy - J_z
        return residual
"""

    pinn_architecture_source_code = """import torch
import torch.nn as nn

class PINNArchitecture(nn.Module):
    def __init__(self, input_dim=2, hidden_layers=4, hidden_neurons=50, output_dim=1):
        super().__init__()
        
        layers = []
        layers.append(nn.Linear(input_dim, hidden_neurons))
        layers.append(nn.SiLU())
        
        for _ in range(hidden_layers - 1):
            layers.append(nn.Linear(hidden_neurons, hidden_neurons))
            layers.append(nn.SiLU())
            
        layers.append(nn.Linear(hidden_neurons, output_dim))
        
        self.network = nn.Sequential(*layers)
        self._initialize_weights()

    def _initialize_weights(self):
        for module in self.network:
            if isinstance(module, nn.Linear):
                nn.init.xavier_normal_(module.weight)
                nn.init.zeros_(module.bias)

    def forward(self, xy, sdf_boundary):
        raw_output = self.network(xy)
        
        A_z = raw_output * sdf_boundary
        return A_z
"""

    training_manager_source_code = """import torch
import torch.optim as optim

class TrainingManager:
    def __init__(self, model, pde_evaluator, lr_adam=1e-3, loss_scaling_factor=1e-6):
        self.model = model
        self.pde_evaluator = pde_evaluator
        self.loss_scaling_factor = loss_scaling_factor
        
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

    def compute_loss(self, points_tensor, signed_distance_field_tensor, reluctivity_tensor, current_density_z_tensor, coercive_field_x_tensor, coercive_field_y_tensor):
        magnetic_vector_potential_z_tensor = self.model(points_tensor, signed_distance_field_tensor)
        
        residual = self.pde_evaluator.compute_residual(
            xy=points_tensor,
            A_z=magnetic_vector_potential_z_tensor,
            nu=reluctivity_tensor,
            J_z=current_density_z_tensor,
            H_cx=coercive_field_x_tensor,
            H_cy=coercive_field_y_tensor
        )
        
        residual_scaled = residual * self.loss_scaling_factor
        loss_pde = torch.mean(residual_scaled**2)
        return loss_pde

    def train_adam(self, epochs, points_tensor, signed_distance_field_tensor, reluctivity_tensor, current_density_z_tensor, coercive_field_x_tensor, coercive_field_y_tensor):
        self.model.train()
        best_loss = float('inf')
        best_model_state = {key: value.cpu().clone() for key, value in self.model.state_dict().items()}
        
        scheduler_adam = optim.lr_scheduler.CosineAnnealingLR(self.optimizer_adam, T_max=epochs, eta_min=1e-6)
        
        for epoch in range(epochs):
            self.optimizer_adam.zero_grad()
            
            loss = self.compute_loss(
                points_tensor, signed_distance_field_tensor, reluctivity_tensor, 
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

    def train_lbfgs(self, epochs, points_tensor, signed_distance_field_tensor, reluctivity_tensor, current_density_z_tensor, coercive_field_x_tensor, coercive_field_y_tensor):
        self.model.train()
        for epoch in range(epochs):
            def closure():
                self.optimizer_lbfgs.zero_grad()
                loss = self.compute_loss(
                    points_tensor, signed_distance_field_tensor, reluctivity_tensor, 
                    current_density_z_tensor, coercive_field_x_tensor, coercive_field_y_tensor
                )
                loss.backward(retain_graph=True)
                return loss
            
            loss_val = self.optimizer_lbfgs.step(closure)
            print(f"L-BFGS Epoch {epoch + 1}: Loss = {loss_val.item():.6e}")
"""

    curriculum_training_manager_source_code = """import torch
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
                signed_distance_field_tensor=signed_distance_field_tensor,
                reluctivity_tensor=reluctivity_tensor,
                current_density_z_tensor=current_density_z_tensor_scaled,
                coercive_field_x_tensor=coercive_field_x_tensor_scaled,
                coercive_field_y_tensor=coercive_field_y_tensor_scaled
            )
            
        print("--- Curriculum L-BFGS Refinement (Alpha = 1.00) ---")
        
        self.training_manager_instance.train_lbfgs(
            epochs=100, 
            points_tensor=points_tensor, 
            signed_distance_field_tensor=signed_distance_field_tensor, 
            reluctivity_tensor=reluctivity_tensor, 
            current_density_z_tensor=current_density_z_tensor, 
            coercive_field_x_tensor=coercive_field_x_tensor, 
            coercive_field_y_tensor=coercive_field_y_tensor
        )
"""

    electro_magnetic_pinn_source_code = """import torch
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
"""

    test_simulation_source_code = """import os
import sys

current_directory = os.path.dirname(os.path.abspath(__file__))
if current_directory not in sys.path:
    sys.path.insert(0, current_directory)

import torch
from geometry_engine.geometry import Geometry
from geometry_engine.segment.segment import Segment
from physics_domain.collocation_sampler import CollocationSampler
from electro_magnetic_pinn import ElectroMagneticPINN

def main():
    geometry_instance = Geometry()
    
    core_vertices = [
        [-0.02, -0.02],
        [0.02, -0.02],
        [0.02, 0.02],
        [-0.02, 0.02]
    ]
    iron_segment = Segment(core_vertices).set_material_properties(
        name="iron_core",
        relative_permeability=1000.0,
        current_density_z_axis=0.0
    )
    geometry_instance.add_segment(iron_segment)
    
    collocation_sampler_instance = CollocationSampler(
        x_boundaries_tuple=(-0.05, 0.05),
        y_boundaries_tuple=(-0.05, 0.05)
    )
    
    model = ElectroMagneticPINN(
        geometry_engine_instance=geometry_instance,
        collocation_sampler_instance=collocation_sampler_instance
    )
    
    model.execute_training_process(
        number_of_uniform_points=200,
        number_of_interface_points=50,
        distance_threshold=0.005,
        stages=2,
        epochs_per_stage=5
    )
    
    test_points = collocation_sampler_instance.generate_uniform_points_tensor(10)
    predictions = model.predict_magnetic_vector_potential(test_points)
    print("Predicted A_z:\\n", predictions)

if __name__ == '__main__':
    main()
"""

    with open(segment_init_file_path, 'w', encoding='utf-8') as segment_init_file_object:
        segment_init_file_object.write(init_source_code)

    with open(polygon_sdf_file_path, 'w', encoding='utf-8') as polygon_sdf_file_object:
        polygon_sdf_file_object.write(polygon_sdf_source_code)

    with open(segment_file_path, 'w', encoding='utf-8') as segment_file_object:
        segment_file_object.write(segment_source_code)

    with open(global_sdf_file_path, 'w', encoding='utf-8') as global_sdf_file_object:
        global_sdf_file_object.write(global_sdf_source_code)
        
    with open(global_properties_file_path, 'w', encoding='utf-8') as global_properties_file_object:
        global_properties_file_object.write(global_properties_source_code)
        
    with open(geometry_file_path, 'w', encoding='utf-8') as geometry_file_object:
        geometry_file_object.write(geometry_source_code)

    with open(collocation_sampler_file_path, 'w', encoding='utf-8') as collocation_sampler_file_object:
        collocation_sampler_file_object.write(collocation_sampler_source_code)

    with open(maxwell_pde_loss_file_path, 'w', encoding='utf-8') as maxwell_pde_loss_file_object:
        maxwell_pde_loss_file_object.write(maxwell_pde_loss_source_code)
        
    with open(pinn_architecture_file_path, 'w', encoding='utf-8') as pinn_architecture_file_object:
        pinn_architecture_file_object.write(pinn_architecture_source_code)
        
    with open(training_manager_file_path, 'w', encoding='utf-8') as training_manager_file_object:
        training_manager_file_object.write(training_manager_source_code)
        
    with open(curriculum_training_manager_file_path, 'w', encoding='utf-8') as curriculum_training_manager_file_object:
        curriculum_training_manager_file_object.write(curriculum_training_manager_source_code)

    with open(electro_magnetic_pinn_file_path, 'w', encoding='utf-8') as electro_magnetic_pinn_file_object:
        electro_magnetic_pinn_file_object.write(electro_magnetic_pinn_source_code)

    with open(test_simulation_file_path, 'w', encoding='utf-8') as test_simulation_file_object:
        test_simulation_file_object.write(test_simulation_source_code)

if __name__ == '__main__':
    modify_project_structure()