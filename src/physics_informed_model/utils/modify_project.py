import os
import shutil

def modify_project_structure():
    base_directory = os.path.dirname(os.path.abspath(__file__))
    project_root_directory = os.path.abspath(os.path.join(base_directory, '..'))
    
    geometry_engine_directory = os.path.join(project_root_directory, 'geometry_engine')
    segment_directory = os.path.join(geometry_engine_directory, 'segment')
    physics_domain_directory = os.path.join(project_root_directory, 'physics_domain')
    physical_equations_directory = os.path.join(physics_domain_directory, 'physical_equations')
    materials_directory = os.path.join(physics_domain_directory, 'materials')
    
    if os.path.exists(materials_directory):
        shutil.rmtree(materials_directory)
        
    old_collocation_file = os.path.join(physics_domain_directory, 'collocation_sampling.py')
    if os.path.exists(old_collocation_file):
        os.remove(old_collocation_file)
        
    old_pnn_file = os.path.join(project_root_directory, 'physics_neural_network.py')
    if os.path.exists(old_pnn_file):
        os.remove(old_pnn_file)

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
    distances_to_edges = torch.norm(points_tensor.unsqueeze(1) - closest_points, dim=2)
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
    y_difference = torch.where(
        torch.abs(y_difference) < torch.finfo(computation_dtype).eps,
        torch.ones_like(y_difference),
        y_difference,
    )
    
    intersection_x_coordinates = start_points_x_coordinates + (points_y_coordinates - start_points_y_coordinates) * (end_points_x_coordinates - start_points_x_coordinates) / y_difference
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
from segment.polygon_signed_distance_field import compute_polygon_signed_distance_field

class Segment:
    def __init__(self, vertices_list=None):
        self.material_name = "air"
        self.vacuum_reluctivity = 795774.715459
        
        self.relative_permeability = 1.0
        self.magnetic_curve_function = None
        
        self.coercive_field_magnitude = 0.0
        self.magnetization_function = None
        
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
        magnetic_curve_function=None, 
        coercive_field_magnitude=0.0, 
        magnetization_function=None, 
        current_density_z_axis=0.0,
        current_density_function=None
    ):
        self.material_name = name
        self.relative_permeability = relative_permeability
        self.magnetic_curve_function = magnetic_curve_function
        self.coercive_field_magnitude = coercive_field_magnitude
        self.magnetization_function = magnetization_function
        self.current_density_z_axis = current_density_z_axis
        self.current_density_function = current_density_function
        return self

    def compute_signed_distance_field(self, points_tensor):
        return compute_polygon_signed_distance_field(self.vertices_tensor, points_tensor)
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
    
    global_relative_permeability_tensor = torch.ones((number_of_points, 1), dtype=torch.float32, device=computation_device)
    global_coercive_field_x_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)
    global_coercive_field_y_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)
    global_current_density_z_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)
    global_material_classification_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)

    material_index_counter = 1.0

    for segment_object in segments_list:
        signed_distance_field = segment_object.compute_signed_distance_field(points_tensor)
        mask_tensor = signed_distance_field <= 0.0
        
        if mask_tensor.any():
            global_relative_permeability_tensor[mask_tensor] = segment_object.relative_permeability
            global_current_density_z_tensor[mask_tensor] = segment_object.current_density_z_axis
            global_coercive_field_x_tensor[mask_tensor] = segment_object.coercive_field_magnitude
            global_material_classification_tensor[mask_tensor] = material_index_counter
        
        material_index_counter += 1.0

    global_reluctivity_tensor = vacuum_reluctivity / global_relative_permeability_tensor

    return {
        "reluctivity": global_reluctivity_tensor,
        "relative_permeability": global_relative_permeability_tensor,
        "coercive_field_x": global_coercive_field_x_tensor,
        "coercive_field_y": global_coercive_field_y_tensor,
        "current_density_z": global_current_density_z_tensor,
        "material_classification": global_material_classification_tensor
    }
"""

    geometry_source_code = """import torch
from segment.segment import Segment
from global_signed_distance_field import compute_global_signed_distance_field
from global_physical_properties_evaluation import evaluate_global_physical_properties

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
        pool_size_value = number_of_points * 20
        points_pool_tensor = torch.rand((pool_size_value, 2), dtype=torch.float32)
        points_pool_tensor[:, 0] = points_pool_tensor[:, 0] * (self.x_maximum - self.x_minimum) + self.x_minimum
        points_pool_tensor[:, 1] = points_pool_tensor[:, 1] * (self.y_maximum - self.y_minimum) + self.y_minimum
        
        signed_distance_field_tensor = geometry_object.compute_global_signed_distance_field(points_pool_tensor)
        
        mask_tensor = torch.abs(signed_distance_field_tensor) < distance_threshold
        mask_tensor_one_dimensional = mask_tensor.squeeze()
        
        interface_points_tensor = points_pool_tensor[mask_tensor_one_dimensional]
        
        if interface_points_tensor.shape[0] > number_of_points:
            interface_points_tensor = interface_points_tensor[:number_of_points, :]
            
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
        layers.append(nn.Tanh())
        
        for _ in range(hidden_layers - 1):
            layers.append(nn.Linear(hidden_neurons, hidden_neurons))
            layers.append(nn.Tanh())
            
        layers.append(nn.Linear(hidden_neurons, output_dim))
        
        self.network = nn.Sequential(*layers)

    def forward(self, xy, sdf_boundary):
        raw_output = self.network(xy)
        
        A_z = raw_output * sdf_boundary
        return A_z
"""

    training_manager_source_code = """import torch
import torch.optim as optim

class TrainingManager:
    def __init__(self, model, pde_evaluator, material_mapping, lr_adam=1e-3):
        self.model = model
        self.pde_evaluator = pde_evaluator
        self.material_mapping = material_mapping
        
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

    def compute_loss(self, xy, sdf_boundary, iron_mask, magnet_mask, slot_masks_dict, slot_current_dict, H_cx, H_cy):
        A_z = self.model(xy, sdf_boundary)
        
        nu = self.material_mapping.get_reluctivity(iron_mask, magnet_mask)
        J_z = self.material_mapping.get_current_density(xy, slot_masks_dict, slot_current_dict)
        
        residual = self.pde_evaluator.compute_residual(xy, A_z, nu, J_z, H_cx, H_cy)
        
        loss_pde = torch.mean(residual**2)
        return loss_pde

    def train_adam(self, epochs, xy, sdf_boundary, iron_mask, magnet_mask, slot_masks_dict, slot_current_dict, H_cx, H_cy):
        self.model.train()
        for epoch in range(epochs):
            self.optimizer_adam.zero_grad()
            
            loss = self.compute_loss(
                xy, sdf_boundary, iron_mask, magnet_mask, 
                slot_masks_dict, slot_current_dict, H_cx, H_cy
            )
            
            loss.backward()
            self.optimizer_adam.step()
            
            if (epoch + 1) % 100 == 0:
                print(f"Adam Epoch {epoch + 1}: Loss = {loss.item():.6e}")

    def train_lbfgs(self, epochs, xy, sdf_boundary, iron_mask, magnet_mask, slot_masks_dict, slot_current_dict, H_cx, H_cy):
        self.model.train()
        for epoch in range(epochs):
            def closure():
                self.optimizer_lbfgs.zero_grad()
                loss = self.compute_loss(
                    xy, sdf_boundary, iron_mask, magnet_mask, 
                    slot_masks_dict, slot_current_dict, H_cx, H_cy
                )
                loss.backward()
                return loss
            
            self.optimizer_lbfgs.step(closure)
            
            loss_val = closure()
            print(f"L-BFGS Epoch {epoch + 1}: Loss = {loss_val.item():.6e}")
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

    for empty_file_path in [electro_magnetic_pinn_file_path, curriculum_training_manager_file_path]:
        if not os.path.exists(empty_file_path):
            with open(empty_file_path, 'w', encoding='utf-8') as f:
                pass

if __name__ == '__main__':
    modify_project_structure()