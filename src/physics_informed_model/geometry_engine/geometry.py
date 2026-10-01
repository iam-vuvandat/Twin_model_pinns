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
        computation_dtype = points_tensor.dtype

        vertices_on_device = self.vertices_tensor.to(
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

if __name__ == "__main__":
    import numpy
    import matplotlib.pyplot
    import matplotlib.colors

    def generate_shifted_circle_vertices_list(radius_value, center_x_coordinate, center_y_coordinate, number_of_points=64):
        angles_array = numpy.linspace(0, 2 * numpy.pi, number_of_points, endpoint=False)
        return [
            [
                center_x_coordinate + radius_value * numpy.cos(angle), 
                center_y_coordinate + radius_value * numpy.sin(angle)
            ] for angle in angles_array
        ]

    square_iron_vertices_list = [[-2.0, 1.0], [-1.0, 1.0], [-1.0, 0.0], [-2.0, 0.0]]
    square_iron_polygon = Polygon().set_vertices(square_iron_vertices_list).set_material_properties(
        name="iron",
        relative_permeability=1000.0
    )

    square_magnet_vertices_list = [[1.0, 1.0], [2.0, 1.0], [2.0, 0.0], [1.0, 0.0]]
    square_magnet_polygon = Polygon().set_vertices(square_magnet_vertices_list).set_material_properties(
        name="magnet",
        relative_permeability=1.05,
        coercive_field_magnitude=800000.0
    )

    circular_wire_vertices_list = generate_shifted_circle_vertices_list(
        radius_value=0.5, 
        center_x_coordinate=0.0, 
        center_y_coordinate=-1.0, 
        number_of_points=64
    )
    circular_wire_polygon = Polygon().set_vertices(circular_wire_vertices_list).set_material_properties(
        name="copper_wire",
        relative_permeability=1.0,
        current_density_z_axis=5000000.0
    )

    combined_test_geometry = square_iron_polygon | square_magnet_polygon | circular_wire_polygon

    spatial_resolution_value = 250
    x_coordinates_array = numpy.linspace(-3.0, 3.0, spatial_resolution_value)
    y_coordinates_array = numpy.linspace(-3.0, 3.0, spatial_resolution_value)
    x_mesh_grid_array, y_mesh_grid_array = numpy.meshgrid(x_coordinates_array, y_coordinates_array)
    
    coordinates_numpy_array = numpy.column_stack((x_mesh_grid_array.ravel(), y_mesh_grid_array.ravel()))
    test_points_tensor = torch.tensor(coordinates_numpy_array, dtype=torch.float32)

    signed_distance_field_tensor = combined_test_geometry.compute_signed_distance_field(test_points_tensor)
    signed_distance_field_grid_array = signed_distance_field_tensor.numpy().reshape(spatial_resolution_value, spatial_resolution_value)

    matplotlib.pyplot.figure(figsize=(8, 7))
    
    minimum_distance_value = signed_distance_field_grid_array.min()
    maximum_distance_value = signed_distance_field_grid_array.max()
    contour_levels_array = numpy.linspace(minimum_distance_value, maximum_distance_value, 60)
    
    color_map_object = matplotlib.colors.LinearSegmentedColormap.from_list("custom_red_white_blue", ["red", "white", "blue"])
    two_slope_normalization_object = matplotlib.colors.TwoSlopeNorm(
        vmin=minimum_distance_value if minimum_distance_value < 0 else -1e-5, 
        vcenter=0.0, 
        vmax=maximum_distance_value if maximum_distance_value > 0 else 1e-5
    )
    
    contour_plot_object = matplotlib.pyplot.contourf(
        x_mesh_grid_array, 
        y_mesh_grid_array, 
        signed_distance_field_grid_array, 
        levels=contour_levels_array, 
        cmap=color_map_object, 
        norm=two_slope_normalization_object
    )
    
    matplotlib.pyplot.contour(
        x_mesh_grid_array, 
        y_mesh_grid_array, 
        signed_distance_field_grid_array, 
        levels=[0.0], 
        colors="black", 
        linewidths=2.0
    )
    
    matplotlib.pyplot.title("Generalized Signed Distance Field: Iron, Magnet, and Wire")
    matplotlib.pyplot.xlabel("x_coordinate")
    matplotlib.pyplot.ylabel("y_coordinate")
    matplotlib.pyplot.axis("equal")
    matplotlib.pyplot.colorbar(contour_plot_object, label="Signed Distance")
    matplotlib.pyplot.tight_layout()
    matplotlib.pyplot.show()
