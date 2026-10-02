import torch

class CollocationSampler:
    def __init__(self, x_boundaries_tuple, y_boundaries_tuple):
        self.x_minimum = x_boundaries_tuple[0]
        self.x_maximum = x_boundaries_tuple[1]
        self.y_minimum = y_boundaries_tuple[0]
        self.y_maximum = y_boundaries_tuple[1]

    def generate_uniform_points_tensor(self, number_of_points):
        points_tensor = torch.rand((number_of_points, 2), dtype=torch.float32)
        points_tensor[:, 0] = points_tensor[:, 0] * (self.x_maximum - self.x_minimum) + self.x_minimum
        points_tensor[:, 1] = points_tensor[:, 1] * (self.y_maximum - self.y_minimum) + self.y_minimum
        points_tensor.requires_grad_(True)
        return points_tensor

    def generate_interface_points_tensor(self, geometry_object, number_of_points, distance_threshold):
        pool_size_value = number_of_points * 20
        points_pool_tensor = torch.rand((pool_size_value, 2), dtype=torch.float32)
        points_pool_tensor[:, 0] = points_pool_tensor[:, 0] * (self.x_maximum - self.x_minimum) + self.x_minimum
        points_pool_tensor[:, 1] = points_pool_tensor[:, 1] * (self.y_maximum - self.y_minimum) + self.y_minimum
        
        signed_distance_field_tensor = geometry_object.compute_global_signed_distance_field(points_pool_tensor)
        
        mask_tensor = torch.abs(signed_distance_field_tensor) < distance_threshold
        mask_tensor_one_dimensional = mask_tensor.squeeze()
        
        interface_points_tensor = points_pool_tensor[mask_tensor_one_dimensional]
        
        if interface_points_tensor.shape[0] > number_of_points:
            interface_points_tensor = interface_points_tensor[:number_of_points, :]
            
        interface_points_tensor = interface_points_tensor.detach().clone()
        interface_points_tensor.requires_grad_(True)
        return interface_points_tensor

    def generate_combined_points_tensor(self, geometry_object, number_of_uniform_points, number_of_interface_points, distance_threshold):
        uniform_points_tensor = self.generate_uniform_points_tensor(number_of_uniform_points)
        interface_points_tensor = self.generate_interface_points_tensor(geometry_object, number_of_interface_points, distance_threshold)
        
        combined_points_tensor = torch.cat([uniform_points_tensor, interface_points_tensor], dim=0)
        
        combined_points_tensor = combined_points_tensor.detach().clone()
        combined_points_tensor.requires_grad_(True)
        return combined_points_tensor
