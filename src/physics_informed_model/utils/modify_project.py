import os

def modify_geometry_engine():
    base_directory = os.path.dirname(os.path.abspath(__file__))
    
    geometry_file_path = os.path.join(base_directory, '..', 'geometry_engine', 'geometry.py')
    geometry_file_path = os.path.abspath(geometry_file_path)

    os.makedirs(os.path.dirname(geometry_file_path), exist_ok=True)

    geometry_source_code = """import torch
from abc import ABC, abstractmethod

class Segment(ABC):
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

    @abstractmethod
    def compute_signed_distance_field(self, points_tensor):
        pass


class PolygonSegment(Segment):
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
            raise ValueError("PolygonSegment vertices must be set before computing signed distance field.")
            
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


class Geometry:
    def __init__(self):
        self.segments_list = []
        self.vacuum_reluctivity = 795774.715459

    def add_segment(self, segment_object):
        self.segments_list.append(segment_object)
        return self

    def compute_global_signed_distance_field(self, points_tensor):
        if not self.segments_list:
            return torch.ones((points_tensor.shape[0], 1), dtype=torch.float32, device=points_tensor.device)
            
        global_signed_distance_field = self.segments_list[0].compute_signed_distance_field(points_tensor)
        
        for segment_object in self.segments_list[1:]:
            current_signed_distance_field = segment_object.compute_signed_distance_field(points_tensor)
            global_signed_distance_field = torch.minimum(global_signed_distance_field, current_signed_distance_field)
            
        return global_signed_distance_field

    def evaluate_global_physical_properties(self, points_tensor):
        number_of_points = points_tensor.shape[0]
        computation_device = points_tensor.device
        
        global_relative_permeability_tensor = torch.ones((number_of_points, 1), dtype=torch.float32, device=computation_device)
        global_coercive_field_x_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)
        global_coercive_field_y_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)
        global_current_density_z_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)
        global_material_classification_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)

        material_index_counter = 1.0

        for segment_object in self.segments_list:
            signed_distance_field = segment_object.compute_signed_distance_field(points_tensor)
            mask_tensor = signed_distance_field <= 0.0
            
            if mask_tensor.any():
                global_relative_permeability_tensor[mask_tensor] = segment_object.relative_permeability
                global_current_density_z_tensor[mask_tensor] = segment_object.current_density_z_axis
                global_coercive_field_x_tensor[mask_tensor] = segment_object.coercive_field_magnitude
                global_material_classification_tensor[mask_tensor] = material_index_counter
            
            material_index_counter += 1.0

        global_reluctivity_tensor = self.vacuum_reluctivity / global_relative_permeability_tensor

        return {
            "reluctivity": global_reluctivity_tensor,
            "relative_permeability": global_relative_permeability_tensor,
            "coercive_field_x": global_coercive_field_x_tensor,
            "coercive_field_y": global_coercive_field_y_tensor,
            "current_density_z": global_current_density_z_tensor,
            "material_classification": global_material_classification_tensor
        }

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
    square_iron_segment = PolygonSegment().set_vertices(square_iron_vertices_list).set_material_properties(
        name="iron",
        relative_permeability=1000.0
    )

    square_magnet_vertices_list = [[1.0, 1.0], [2.0, 1.0], [2.0, 0.0], [1.0, 0.0]]
    square_magnet_segment = PolygonSegment().set_vertices(square_magnet_vertices_list).set_material_properties(
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
    circular_wire_segment = PolygonSegment().set_vertices(circular_wire_vertices_list).set_material_properties(
        name="copper_wire",
        relative_permeability=1.0,
        current_density_z_axis=5000000.0
    )

    computational_domain_geometry = Geometry()
    computational_domain_geometry.add_segment(square_iron_segment)
    computational_domain_geometry.add_segment(square_magnet_segment)
    computational_domain_geometry.add_segment(circular_wire_segment)

    spatial_resolution_value = 250
    x_coordinates_array = numpy.linspace(-3.0, 3.0, spatial_resolution_value)
    y_coordinates_array = numpy.linspace(-3.0, 3.0, spatial_resolution_value)
    x_mesh_grid_array, y_mesh_grid_array = numpy.meshgrid(x_coordinates_array, y_coordinates_array)
    
    coordinates_numpy_array = numpy.column_stack((x_mesh_grid_array.ravel(), y_mesh_grid_array.ravel()))
    test_points_tensor = torch.tensor(coordinates_numpy_array, dtype=torch.float32)

    global_signed_distance_field_tensor = computational_domain_geometry.compute_global_signed_distance_field(test_points_tensor)
    physical_properties_dictionary = computational_domain_geometry.evaluate_global_physical_properties(test_points_tensor)

    signed_distance_field_grid_array = global_signed_distance_field_tensor.numpy().reshape(spatial_resolution_value, spatial_resolution_value)
    material_classification_grid_array = physical_properties_dictionary["material_classification"].numpy().reshape(spatial_resolution_value, spatial_resolution_value)
    relative_permeability_grid_array = physical_properties_dictionary["relative_permeability"].numpy().reshape(spatial_resolution_value, spatial_resolution_value)
    coercive_field_x_grid_array = physical_properties_dictionary["coercive_field_x"].numpy().reshape(spatial_resolution_value, spatial_resolution_value)
    coercive_field_y_grid_array = physical_properties_dictionary["coercive_field_y"].numpy().reshape(spatial_resolution_value, spatial_resolution_value)
    current_density_z_grid_array = physical_properties_dictionary["current_density_z"].numpy().reshape(spatial_resolution_value, spatial_resolution_value)

    figure_object, axes_array = matplotlib.pyplot.subplots(nrows=2, ncols=3, figsize=(18, 12))
    
    color_map_signed_distance_field = matplotlib.colors.LinearSegmentedColormap.from_list("custom_red_white_blue", ["red", "white", "blue"])
    two_slope_normalization_object = matplotlib.colors.TwoSlopeNorm(
        vmin=signed_distance_field_grid_array.min() if signed_distance_field_grid_array.min() < 0 else -1e-5, 
        vcenter=0.0, 
        vmax=signed_distance_field_grid_array.max() if signed_distance_field_grid_array.max() > 0 else 1e-5
    )
    
    contour_plot_signed_distance_field = axes_array[0, 0].contourf(
        x_mesh_grid_array, y_mesh_grid_array, signed_distance_field_grid_array, 
        levels=60, cmap=color_map_signed_distance_field, norm=two_slope_normalization_object
    )
    axes_array[0, 0].contour(x_mesh_grid_array, y_mesh_grid_array, signed_distance_field_grid_array, levels=[0.0], colors="black", linewidths=1.5)
    axes_array[0, 0].set_title("Global Signed Distance Field")
    axes_array[0, 0].set_aspect("equal")
    figure_object.colorbar(contour_plot_signed_distance_field, ax=axes_array[0, 0], label="Distance (m)")

    color_map_material = matplotlib.colors.ListedColormap(["white", "gray", "red", "orange"])
    contour_plot_material = axes_array[0, 1].contourf(
        x_mesh_grid_array, y_mesh_grid_array, material_classification_grid_array, 
        levels=[-0.5, 0.5, 1.5, 2.5, 3.5], cmap=color_map_material
    )
    axes_array[0, 1].set_title("Material Classification")
    axes_array[0, 1].set_aspect("equal")
    color_bar_material = figure_object.colorbar(contour_plot_material, ax=axes_array[0, 1], ticks=[0, 1, 2, 3])
    color_bar_material.ax.set_yticklabels(["Air", "Iron", "Magnet", "Copper Wire"])

    contour_plot_permeability = axes_array[0, 2].contourf(
        x_mesh_grid_array, y_mesh_grid_array, relative_permeability_grid_array, 
        levels=60, cmap="viridis"
    )
    axes_array[0, 2].set_title("Relative Permeability")
    axes_array[0, 2].set_aspect("equal")
    figure_object.colorbar(contour_plot_permeability, ax=axes_array[0, 2], label="Permeability Value")

    contour_plot_current = axes_array[1, 0].contourf(
        x_mesh_grid_array, y_mesh_grid_array, current_density_z_grid_array, 
        levels=60, cmap="plasma"
    )
    axes_array[1, 0].set_title("Current Density Z-Axis")
    axes_array[1, 0].set_aspect("equal")
    figure_object.colorbar(contour_plot_current, ax=axes_array[1, 0], label="Current Density (A/m^2)")

    contour_plot_coercive_x = axes_array[1, 1].contourf(
        x_mesh_grid_array, y_mesh_grid_array, coercive_field_x_grid_array, 
        levels=60, cmap="coolwarm"
    )
    axes_array[1, 1].set_title("Coercive Field X-Axis")
    axes_array[1, 1].set_aspect("equal")
    figure_object.colorbar(contour_plot_coercive_x, ax=axes_array[1, 1], label="Magnetic Field (A/m)")

    contour_plot_coercive_y = axes_array[1, 2].contourf(
        x_mesh_grid_array, y_mesh_grid_array, coercive_field_y_grid_array, 
        levels=60, cmap="coolwarm"
    )
    axes_array[1, 2].set_title("Coercive Field Y-Axis")
    axes_array[1, 2].set_aspect("equal")
    figure_object.colorbar(contour_plot_coercive_y, ax=axes_array[1, 2], label="Magnetic Field (A/m)")

    matplotlib.pyplot.tight_layout()
    matplotlib.pyplot.show()
"""
    
    with open(geometry_file_path, 'w', encoding='utf-8') as file_object:
        file_object.write(geometry_source_code)

if __name__ == "__main__":
    modify_geometry_engine()