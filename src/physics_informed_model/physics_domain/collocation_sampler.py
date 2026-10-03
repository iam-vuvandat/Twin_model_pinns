import torch

class CollocationSampler:
    def __init__(self, x_boundaries_tuple, y_boundaries_tuple):
        self.x_minimum = x_boundaries_tuple[0]
        self.x_maximum = x_boundaries_tuple[1]
        self.y_minimum = y_boundaries_tuple[0]
        self.y_maximum = y_boundaries_tuple[1]
        # Khởi tạo engine tạo số giả ngẫu nhiên phân bố đều (Sobol)
        self.sobol_engine = torch.quasirandom.SobolEngine(dimension=2, scramble=True)

    def generate_uniform_points_tensor(self, number_of_points):
        sobol_points = self.sobol_engine.draw(number_of_points)
        points_tensor = torch.zeros_like(sobol_points, dtype=torch.float32)
        points_tensor[:, 0] = sobol_points[:, 0] * (self.x_maximum - self.x_minimum) + self.x_minimum
        points_tensor[:, 1] = sobol_points[:, 1] * (self.y_maximum - self.y_minimum) + self.y_minimum
        points_tensor.requires_grad_(True)
        return points_tensor

    def generate_interface_points_tensor(self, geometry_object, number_of_points, distance_threshold, max_attempts=50):
        collected_points = []
        collected_count = 0
        pool_size_value = number_of_points * 20
        attempts = 0
        
        while collected_count < number_of_points and attempts < max_attempts:
            attempts += 1
            sobol_pool = self.sobol_engine.draw(pool_size_value)
            points_pool_tensor = torch.zeros_like(sobol_pool, dtype=torch.float32)
            points_pool_tensor[:, 0] = sobol_pool[:, 0] * (self.x_maximum - self.x_minimum) + self.x_minimum
            points_pool_tensor[:, 1] = sobol_pool[:, 1] * (self.y_maximum - self.y_minimum) + self.y_minimum
            
            signed_distance_field_tensor = geometry_object.compute_global_signed_distance_field(points_pool_tensor)
            mask_tensor = torch.abs(signed_distance_field_tensor) < distance_threshold
            mask_1d = mask_tensor.squeeze()
            
            if mask_1d.any():
                valid_points = points_pool_tensor[mask_1d]
                collected_points.append(valid_points)
                collected_count += valid_points.shape[0]
                
        if attempts == max_attempts and collected_count < number_of_points:
            print(f"[CẢNH BÁO] Lấy mẫu Interface đạt max_attempts ({max_attempts}). Chỉ thu được {collected_count}/{number_of_points} điểm.")
            
        if collected_count == 0:
            return self.generate_uniform_points_tensor(number_of_points)

        interface_points_tensor = torch.cat(collected_points, dim=0)[:number_of_points, :]
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
