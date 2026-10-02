import os
import shutil

def modify_project_structure():
    base_directory = os.path.dirname(os.path.abspath(__file__))
    project_root_directory = os.path.abspath(os.path.join(base_directory, '..'))
    
    geometry_engine_directory = os.path.join(project_root_directory, 'geometry_engine')
    templates_directory = os.path.join(geometry_engine_directory, 'templates')
    
    physics_domain_directory = os.path.join(project_root_directory, 'physics_domain')
    materials_directory = os.path.join(physics_domain_directory, 'materials')
    physical_equations_directory = os.path.join(physics_domain_directory, 'physical_equations')
    
    # 6. XÓA MÃ NGUỒN RỖNG (DEAD CODE)
    for dead_file in ['physics_neural_network.py', 'trial_function_wrapper.py']:
        dead_path = os.path.join(project_root_directory, dead_file)
        if os.path.exists(dead_path):
            os.remove(dead_path)
            
    os.makedirs(geometry_engine_directory, exist_ok=True)
    os.makedirs(templates_directory, exist_ok=True)
    os.makedirs(physics_domain_directory, exist_ok=True)
    os.makedirs(materials_directory, exist_ok=True)
    os.makedirs(physical_equations_directory, exist_ok=True)

    # ĐỊNH NGHĨA ĐƯỜNG DẪN TỆP
    curriculum_training_manager_file_path = os.path.join(project_root_directory, 'curriculum_training_manager.py')
    pinn_architecture_file_path = os.path.join(project_root_directory, 'pinn_architecture.py')
    training_manager_file_path = os.path.join(project_root_directory, 'training_manager.py')
    
    geometry_file_path = os.path.join(geometry_engine_directory, 'geometry.py')
    templates_init_file_path = os.path.join(templates_directory, '__init__.py')
    u_shape_magnet_template_file_path = os.path.join(templates_directory, 'u_shape_magnet_template.py')
    
    collocation_sampling_file_path = os.path.join(physics_domain_directory, 'collocation_sampling.py')
    material_permeability_properties_file_path = os.path.join(materials_directory, 'material_permeability_properties.py')
    maxwell_pde_loss_file_path = os.path.join(physical_equations_directory, 'maxwell_pde_loss.py')

    curriculum_training_manager_source_code = """import torch
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
            
            loss.backward(retain_graph=True)
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
                loss.backward(retain_graph=True)
                return loss
            
            # 2. SỬA LỖI HIỆU SUẤT L-BFGS: Không gọi closure() lần thứ 2
            loss_val = self.optimizer_lbfgs.step(closure)
            print(f"L-BFGS Epoch {epoch + 1}: Loss = {loss_val.item():.6e}")
"""

    geometry_source_code = """import torch
from abc import ABC, abstractmethod
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

class Geometry(ABC):
    def __init__(self, material_name=None):
        self.material_name = material_name

    def set_material(self, material_name):
        self.material_name = material_name
        return self

    @abstractmethod
    def compute_sdf(self, points):
        pass

    def __or__(self, other):
        return BooleanUnion(self, other)

    def __and__(self, other):
        return BooleanIntersection(self, other)

    def __sub__(self, other):
        return BooleanDifference(self, other)

class Polygon(Geometry):
    def __init__(self, vertices=None, material_name=None):
        super().__init__(material_name)
        self.vertices = None
        if vertices is not None:
            self.set_vertices(vertices)

    def set_vertices(self, vertices):
        self.vertices = torch.tensor(vertices, dtype=torch.float32)
        return self

    def compute_sdf(self, points):
        if self.vertices is None:
            raise ValueError("Polygon vertices must be set before computing SDF.")
            
        device = points.device
        V = self.vertices.to(device)
        
        A = V
        B = torch.roll(V, shifts=-1, dims=0)
        
        AB = B - A
        AP = points.unsqueeze(1) - A.unsqueeze(0)
        
        dot_AP_AB = torch.sum(AP * AB.unsqueeze(0), dim=2)
        dot_AB_AB = torch.sum(AB * AB, dim=1).unsqueeze(0)
        t = dot_AP_AB / dot_AB_AB
        t_clamped = torch.clamp(t, min=0.0, max=1.0)
        
        closest_points = A.unsqueeze(0) + t_clamped.unsqueeze(-1) * AB.unsqueeze(0)
        distances = torch.norm(points.unsqueeze(1) - closest_points, dim=2)
        min_distances, _ = torch.min(distances, dim=1)
        
        Px = points[:, 0].unsqueeze(1)
        Py = points[:, 1].unsqueeze(1)
        Ax = A[:, 0].unsqueeze(0)
        Ay = A[:, 1].unsqueeze(0)
        Bx = B[:, 0].unsqueeze(0)
        By = B[:, 1].unsqueeze(0)
        
        cond1 = (Ay <= Py) & (Py < By)
        cond2 = (By <= Py) & (Py < Ay)
        valid_y = cond1 | cond2
        
        # 1. SỬA LỖI CHIA CHO 0: Bảo vệ mẫu số khỏi giá trị 0
        dy = By - Ay
        dy_safe = torch.where(torch.abs(dy) < 1e-7, torch.full_like(dy, 1e-7), dy)
        intersect_x = Ax + (Py - Ay) * (Bx - Ax) / dy_safe
        
        crossings = valid_y & (Px < intersect_x)
        
        inside = crossings.sum(dim=1) % 2 == 1
        sign = torch.where(inside, -1.0, 1.0)
        
        return sign * min_distances

# 5. SỬA LỖI KẾ THỪA OOP: Bổ sung material_name cho các khối Boolean
class BooleanUnion(Geometry):
    def __init__(self, geom1, geom2, material_name=None):
        super().__init__(material_name)
        self.geom1 = geom1
        self.geom2 = geom2

    def compute_sdf(self, points):
        sdf1 = self.geom1.compute_sdf(points)
        sdf2 = self.geom2.compute_sdf(points)
        return torch.minimum(sdf1, sdf2)

class BooleanIntersection(Geometry):
    def __init__(self, geom1, geom2, material_name=None):
        super().__init__(material_name)
        self.geom1 = geom1
        self.geom2 = geom2

    def compute_sdf(self, points):
        sdf1 = self.geom1.compute_sdf(points)
        sdf2 = self.geom2.compute_sdf(points)
        return torch.maximum(sdf1, sdf2)

class BooleanDifference(Geometry):
    def __init__(self, geom1, geom2, material_name=None):
        super().__init__(material_name)
        self.geom1 = geom1
        self.geom2 = geom2

    def compute_sdf(self, points):
        sdf1 = self.geom1.compute_sdf(points)
        sdf2 = self.geom2.compute_sdf(points)
        return torch.maximum(sdf1, -sdf2)

def evaluate_generalized_sdf(points, geometry: Geometry):
    return geometry.compute_sdf(points)

def get_subdomain_material_masks(points, geometry_dict):
    device = points.device
    masks = {}
    for mat_name, geom in geometry_dict.items():
        sdf_vals = geom.compute_sdf(points)
        masks[mat_name] = (sdf_vals <= 0).to(torch.float32)
    return masks
"""

    u_shape_magnet_template_source_code = """import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

import torch
from src.physics_informed_model.geometry_engine.geometry import Polygon

class UShapeMagnetTemplate:
    def __init__(self, width, height, thickness, air_box_size=5.0, material="magnet"):
        self.width = width
        self.height = height
        self.thickness = thickness
        self.air_box_size = air_box_size
        self.material = material

    def build(self):
        air_box = Polygon().set_material("air").set_vertices([
            [-self.air_box_size/2, self.air_box_size/2],
            [self.air_box_size/2, self.air_box_size/2],
            [self.air_box_size/2, -self.air_box_size/2],
            [-self.air_box_size/2, -self.air_box_size/2]
        ])
        
        outer_rect = Polygon().set_vertices([
            [-self.width/2, self.height/2],
            [self.width/2, self.height/2],
            [self.width/2, -self.height/2],
            [-self.width/2, -self.height/2]
        ])
        
        inner_rect = Polygon().set_vertices([
            [-(self.width/2 - self.thickness), self.height/2],
            [(self.width/2 - self.thickness), self.height/2],
            [(self.width/2 - self.thickness), -self.height/2 + self.thickness],
            [-(self.width/2 - self.thickness), -self.height/2 + self.thickness]
        ])
        
        magnet_u_shape = outer_rect - inner_rect
        magnet_u_shape.set_material(self.material)
        
        air_domain = air_box - magnet_u_shape
        
        return air_domain, magnet_u_shape, air_box
"""

    collocation_sampling_source_code = """import torch

class CollocationSampler:
    def __init__(self, x_bounds, y_bounds):
        self.x_min, self.x_max = x_bounds
        self.y_min, self.y_max = y_bounds

    def generate_uniform_points(self, num_points):
        xy = torch.rand((num_points, 2))
        xy[:, 0] = xy[:, 0] * (self.x_max - self.x_min) + self.x_min
        xy[:, 1] = xy[:, 1] * (self.y_max - self.y_min) + self.y_min
        xy.requires_grad_(True)
        return xy

    def generate_interface_points(self, geometry, num_points, epsilon):
        # 3. SỬA LỖI THIẾU HỤT ĐIỂM: Vòng lặp bù điểm
        collected_points = []
        collected_count = 0
        pool_size = num_points * 20
        
        while collected_count < num_points:
            xy_pool = torch.rand((pool_size, 2))
            xy_pool[:, 0] = xy_pool[:, 0] * (self.x_max - self.x_min) + self.x_min
            xy_pool[:, 1] = xy_pool[:, 1] * (self.y_max - self.y_min) + self.y_min
            
            sdf_vals = geometry.compute_sdf(xy_pool)
            mask = torch.abs(sdf_vals) < epsilon
            mask_1d = mask.squeeze()
            
            if mask_1d.any():
                valid_points = xy_pool[mask_1d]
                collected_points.append(valid_points)
                collected_count += valid_points.shape[0]
                
        xy_interface = torch.cat(collected_points, dim=0)[:num_points, :]
        xy_interface = xy_interface.detach().clone()
        xy_interface.requires_grad_(True)
        return xy_interface

    def generate_combined_points(self, geometry, num_uniform, num_interface, epsilon):
        xy_uniform = self.generate_uniform_points(num_uniform)
        xy_interface = self.generate_interface_points(geometry, num_interface, epsilon)
        
        xy_combined = torch.cat([xy_uniform, xy_interface], dim=0)
        
        xy_combined = xy_combined.detach().clone()
        xy_combined.requires_grad_(True)
        return xy_combined
"""

    material_permeability_properties_source_code = """import torch

class MaterialMapping:
    def __init__(self, nu_0=795774.715459, mu_r_iron=1000.0, mu_r_magnet=1.05):
        self.nu_0 = nu_0
        self.nu_iron = nu_0 / mu_r_iron
        self.nu_magnet = nu_0 / mu_r_magnet

    def get_reluctivity(self, iron_mask, magnet_mask):
        # 4. SỬA LỖI GIAO NHAU MẶT NẠ: Kẹp giá trị air_mask tránh số âm
        overlap_mask = iron_mask + magnet_mask
        air_mask = torch.clamp(1.0 - overlap_mask, min=0.0, max=1.0)
        
        nu_out = iron_mask * self.nu_iron + magnet_mask * self.nu_magnet + air_mask * self.nu_0
        return nu_out

    def get_current_density(self, points, slot_masks_dict, slot_current_dict):
        device = points.device
        dtype = points.dtype
        J_z = torch.zeros((points.shape[0], 1), device=device, dtype=dtype)
        
        for slot_name, mask in slot_masks_dict.items():
            if slot_name in slot_current_dict:
                current_value = slot_current_dict[slot_name]
                J_z += mask * current_value
                
        return J_z
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

    with open(curriculum_training_manager_file_path, 'w', encoding='utf-8') as f: f.write(curriculum_training_manager_source_code)
    with open(pinn_architecture_file_path, 'w', encoding='utf-8') as f: f.write(pinn_architecture_source_code)
    with open(training_manager_file_path, 'w', encoding='utf-8') as f: f.write(training_manager_source_code)
    with open(geometry_file_path, 'w', encoding='utf-8') as f: f.write(geometry_source_code)
    with open(templates_init_file_path, 'w', encoding='utf-8') as f: f.write("")
    with open(u_shape_magnet_template_file_path, 'w', encoding='utf-8') as f: f.write(u_shape_magnet_template_source_code)
    with open(collocation_sampling_file_path, 'w', encoding='utf-8') as f: f.write(collocation_sampling_source_code)
    with open(material_permeability_properties_file_path, 'w', encoding='utf-8') as f: f.write(material_permeability_properties_source_code)
    with open(maxwell_pde_loss_file_path, 'w', encoding='utf-8') as f: f.write(maxwell_pde_loss_source_code)

if __name__ == '__main__':
    modify_project_structure()