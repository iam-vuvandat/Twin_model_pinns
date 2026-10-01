import torch
from segment import Segment, PolygonSegment

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
