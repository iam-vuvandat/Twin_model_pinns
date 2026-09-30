import torch

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
        pool_size = num_points * 20
        xy_pool = torch.rand((pool_size, 2))
        xy_pool[:, 0] = xy_pool[:, 0] * (self.x_max - self.x_min) + self.x_min
        xy_pool[:, 1] = xy_pool[:, 1] * (self.y_max - self.y_min) + self.y_min
        
        sdf_vals = geometry.compute_sdf(xy_pool)
        
        mask = torch.abs(sdf_vals) < epsilon
        xy_interface = xy_pool[mask]
        
        if xy_interface.shape[0] > num_points:
            xy_interface = xy_interface[:num_points, :]
            
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