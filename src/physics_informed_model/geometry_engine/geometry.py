import torch
from abc import ABC, abstractmethod

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
        
        intersect_x = Ax + (Py - Ay) * (Bx - Ax) / (By - Ay)
        crossings = valid_y & (Px < intersect_x)
        
        inside = crossings.sum(dim=1) % 2 == 1
        sign = torch.where(inside, -1.0, 1.0)
        
        return sign * min_distances


class BooleanUnion(Geometry):
    def __init__(self, geom1, geom2):
        super().__init__()
        self.geom1 = geom1
        self.geom2 = geom2

    def compute_sdf(self, points):
        sdf1 = self.geom1.compute_sdf(points)
        sdf2 = self.geom2.compute_sdf(points)
        return torch.minimum(sdf1, sdf2)


class BooleanIntersection(Geometry):
    def __init__(self, geom1, geom2):
        super().__init__()
        self.geom1 = geom1
        self.geom2 = geom2

    def compute_sdf(self, points):
        sdf1 = self.geom1.compute_sdf(points)
        sdf2 = self.geom2.compute_sdf(points)
        return torch.maximum(sdf1, sdf2)


class BooleanDifference(Geometry):
    def __init__(self, geom1, geom2):
        super().__init__()
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


if __name__ == "__main__":
    import numpy as np
    import matplotlib.pyplot as plt

    base_rect_vertices = [
        [-2.0, 2.0], [2.0, 2.0], [2.0, -2.0], [-2.0, -2.0]
    ]
    slot_vertices = [
        [-0.5, 2.0], [0.5, 2.0], [0.5, 0.5], [-0.5, 0.5]
    ]
    
    stator_base = Polygon().set_material("iron").set_vertices(base_rect_vertices)
    slot_air = Polygon().set_material("air").set_vertices(slot_vertices)
    
    stator_with_slot = stator_base - slot_air

    resolution = 250
    x = np.linspace(-2.5, 2.5, resolution)
    y = np.linspace(-2.5, 2.5, resolution)
    X, Y = np.meshgrid(x, y)
    
    xy_np = np.column_stack((X.ravel(), Y.ravel()))
    test_points = torch.tensor(xy_np, dtype=torch.float32)

    sdf_machine = evaluate_generalized_sdf(test_points, stator_with_slot)
    SDF_grid = sdf_machine.numpy().reshape(resolution, resolution)

    plt.figure(figsize=(7, 6))
    contour = plt.contourf(X, Y, SDF_grid, levels=60, cmap="coolwarm")
    plt.contour(X, Y, SDF_grid, levels=[0.0], colors="black", linewidths=2.5)
    
    plt.title("Generalized SDF: Complex Stator Using Polygon & Boolean Ops")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.axis("equal")
    plt.colorbar(contour, label="Distance")
    plt.tight_layout()
    plt.show()