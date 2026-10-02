import sys
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
