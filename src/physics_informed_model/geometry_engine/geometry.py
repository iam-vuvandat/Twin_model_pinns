import torch
from abc import ABC, abstractmethod

class Geometry(ABC):
    def __init__(self):
        self.material_name = "air"
        self.vacuum_reluctivity = 795774.715459
        
        self.relative_permeability = 1.0
        self.magnetic_curve_function = None
        
        self.coercive_field_magnitude = 0.0
        self.magnetization_function = None
        
        self.current_density_z_axis = 0.0
        self.current_density_function = None

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

    def get_reluctivity(self, magnetic_flux_density_squared=None):
        if self.magnetic_curve_function is not None and magnetic_flux_density_squared is not None:
            return self.magnetic_curve_function(magnetic_flux_density_squared)
        return self.vacuum_reluctivity / self.relative_permeability

    def get_magnetization(self, coordinates, mask_tensor):
        if self.coercive_field_magnitude == 0.0:
            return torch.zeros_like(mask_tensor), torch.zeros_like(mask_tensor)
        
        if self.magnetization_function is not None:
            return self.magnetization_function(coordinates, mask_tensor, self.coercive_field_magnitude)
            
        coercive_field_x_axis = torch.zeros_like(mask_tensor)
        coercive_field_y_axis = torch.zeros_like(mask_tensor)
        coercive_field_x_axis += self.coercive_field_magnitude 
        return coercive_field_x_axis, coercive_field_y_axis

    def get_current_density(self, coordinates, mask_tensor):
        if self.current_density_z_axis == 0.0 and self.current_density_function is None:
            return torch.zeros_like(mask_tensor)
            
        if self.current_density_function is not None:
            return self.current_density_function(coordinates, mask_tensor, self.current_density_z_axis)
            
        return torch.ones_like(mask_tensor) * self.current_density_z_axis

    @abstractmethod
    def compute_signed_distance_field(self, points_tensor):
        pass

    @staticmethod
    def _inherit_properties(target_geometry, source_geometry):
        target_geometry.set_material_properties(
            name=source_geometry.material_name,
            relative_permeability=source_geometry.relative_permeability,
            magnetic_curve_function=source_geometry.magnetic_curve_function,
            coercive_field_magnitude=source_geometry.coercive_field_magnitude,
            magnetization_function=source_geometry.magnetization_function,
            current_density_z_axis=source_geometry.current_density_z_axis,
            current_density_function=source_geometry.current_density_function
        )

    def __or__(self, other_geometry):
        result_geometry = BooleanUnion(self, other_geometry)
        self._inherit_properties(result_geometry, self)
        return result_geometry

    def __and__(self, other_geometry):
        result_geometry = BooleanIntersection(self, other_geometry)
        self._inherit_properties(result_geometry, self)
        return result_geometry

    def __sub__(self, other_geometry):
        result_geometry = BooleanDifference(self, other_geometry)
        self._inherit_properties(result_geometry, self)
        return result_geometry

class Polygon(Geometry):
    def __init__(self, vertices_list=None):
        super().__init__()
        self.vertices_tensor = None
        if vertices_list is not None:
            self.set_vertices(vertices_list)

    def set_vertices(self, vertices_list):
        self.vertices_tensor = torch.tensor(vertices_list, dtype=torch.float32)
        return self

    def compute_signed_distance_field(self, points_tensor):
        if self.vertices_tensor is None:
            raise ValueError("Polygon vertices must be set before computing signed distance field.")
            
        computation_device = points_tensor.device
        vertices_on_device = self.vertices_tensor.to(computation_device)
        
        start_points = vertices_on_device
        end_points = torch.roll(vertices_on_device, shifts=-1, dims=0)
        
        edge_vectors = end_points - start_points
        point_to_start_vectors = points_tensor.unsqueeze(1) - start_points.unsqueeze(0)
        
        dot_product_point_to_start_and_edge = torch.sum(point_to_start_vectors * edge_vectors.unsqueeze(0), dim=2)
        dot_product_edge_and_edge = torch.sum(edge_vectors * edge_vectors, dim=1).unsqueeze(0)
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
        
        intersection_x_coordinates = start_points_x_coordinates + (points_y_coordinates - start_points_y_coordinates) * (end_points_x_coordinates - start_points_x_coordinates) / (end_points_y_coordinates - start_points_y_coordinates)
        ray_crossings = valid_y_intersection & (points_x_coordinates < intersection_x_coordinates)
        
        is_point_inside = ray_crossings.sum(dim=1) % 2 == 1
        distance_sign = torch.where(is_point_inside, -1.0, 1.0)
        
        return distance_sign * minimum_distances

class BooleanUnion(Geometry):
    def __init__(self, geometry_one, geometry_two):
        super().__init__()
        self.geometry_one = geometry_one
        self.geometry_two = geometry_two

    def compute_signed_distance_field(self, points_tensor):
        signed_distance_field_one = self.geometry_one.compute_signed_distance_field(points_tensor)
        signed_distance_field_two = self.geometry_two.compute_signed_distance_field(points_tensor)
        return torch.minimum(signed_distance_field_one, signed_distance_field_two)

class BooleanIntersection(Geometry):
    def __init__(self, geometry_one, geometry_two):
        super().__init__()
        self.geometry_one = geometry_one
        self.geometry_two = geometry_two

    def compute_signed_distance_field(self, points_tensor):
        signed_distance_field_one = self.geometry_one.compute_signed_distance_field(points_tensor)
        signed_distance_field_two = self.geometry_two.compute_signed_distance_field(points_tensor)
        return torch.maximum(signed_distance_field_one, signed_distance_field_two)

class BooleanDifference(Geometry):
    def __init__(self, geometry_one, geometry_two):
        super().__init__()
        self.geometry_one = geometry_one
        self.geometry_two = geometry_two

    def compute_signed_distance_field(self, points_tensor):
        signed_distance_field_one = self.geometry_one.compute_signed_distance_field(points_tensor)
        signed_distance_field_two = self.geometry_two.compute_signed_distance_field(points_tensor)
        return torch.maximum(signed_distance_field_one, -signed_distance_field_two)
