import torch
from abc import ABC, abstractmethod
from functions.polygon_sdf import compute_polygon_signed_distance_field

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
        return compute_polygon_signed_distance_field(self.vertices_tensor, points_tensor)
