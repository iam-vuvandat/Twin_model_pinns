import torch
from abc import ABC, abstractmethod

class Geometry(ABC):
    def __init__(self):
        self.material_name = "air"
        self.nu_0 = 795774.715459
        
        self.mu_r = 1.0
        self.bh_curve_fn = None
        
        self.Hc_magnitude = 0.0
        self.magnetization_fn = None
        
        self.J_z = 0.0
        self.current_density_fn = None

    def set_material_properties(
        self, 
        name="default", 
        mu_r=1.0, 
        bh_curve_fn=None, 
        Hc_magnitude=0.0, 
        magnetization_fn=None, 
        J_z=0.0,
        current_density_fn=None
    ):
        self.material_name = name
        self.mu_r = mu_r
        self.bh_curve_fn = bh_curve_fn
        self.Hc_magnitude = Hc_magnitude
        self.magnetization_fn = magnetization_fn
        self.J_z = J_z
        self.current_density_fn = current_density_fn
        return self

    def get_reluctivity(self, B_squared=None):
        if self.bh_curve_fn is not None and B_squared is not None:
            return self.bh_curve_fn(B_squared)
        return self.nu_0 / self.mu_r

    def get_magnetization(self, xy, mask):
        if self.Hc_magnitude == 0.0:
            return torch.zeros_like(mask), torch.zeros_like(mask)
        
        if self.magnetization_fn is not None:
            return self.magnetization_fn(xy, mask, self.Hc_magnitude)
            
        H_cx = torch.zeros_like(mask)
        H_cy = torch.zeros_like(mask)
        H_cx += self.Hc_magnitude 
        return H_cx, H_cy

    def get_current_density(self, xy, mask):
        if self.J_z == 0.0 and self.current_density_fn is None:
            return torch.zeros_like(mask)
            
        if self.current_density_fn is not None:
            return self.current_density_fn(xy, mask, self.J_z)
            
        return torch.ones_like(mask) * self.J_z

    @abstractmethod
    def compute_sdf(self, points):
        pass

    @staticmethod
    def _inherit_properties(target, source):
        target.set_material_properties(
            name=source.material_name,
            mu_r=source.mu_r,
            bh_curve_fn=source.bh_curve_fn,
            Hc_magnitude=source.Hc_magnitude,
            magnetization_fn=source.magnetization_fn,
            J_z=source.J_z,
            current_density_fn=source.current_density_fn
        )

    def __or__(self, other):
        result = BooleanUnion(self, other)
        self._inherit_properties(result, self)
        return result

    def __and__(self, other):
        result = BooleanIntersection(self, other)
        self._inherit_properties(result, self)
        return result

    def __sub__(self, other):
        result = BooleanDifference(self, other)
        self._inherit_properties(result, self)
        return result

class Polygon(Geometry):
    def __init__(self, vertices=None):
        super().__init__()
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
