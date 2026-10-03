import torch
import torch.nn as nn

class PINNArchitecture(nn.Module):
    def __init__(self, input_dim=2, hidden_layers=4, hidden_neurons=50, output_dim=1, x_bounds=(-0.05, 0.05), y_bounds=(-0.05, 0.05)):
        super().__init__()
        self.x_min, self.x_max = x_bounds
        self.y_min, self.y_max = y_bounds
        
        layers = []
        layers.append(nn.Linear(input_dim, hidden_neurons))
        layers.append(nn.Tanh())
        
        for _ in range(hidden_layers - 1):
            layers.append(nn.Linear(hidden_neurons, hidden_neurons))
            layers.append(nn.Tanh())
            
        layers.append(nn.Linear(hidden_neurons, output_dim))
        
        self.network = nn.Sequential(*layers)
        self._initialize_weights()

    def _initialize_weights(self):
        for module in self.network:
            if isinstance(module, nn.Linear):
                nn.init.xavier_normal_(module.weight)
                nn.init.zeros_(module.bias)

    def boundary_factor(self, xy):
        # Chuyển đổi tọa độ thành xi, eta trong khoảng [-1, 1]
        xi = (2.0 * xy[:, 0:1] - (self.x_max + self.x_min)) / (self.x_max - self.x_min)
        eta = (2.0 * xy[:, 1:2] - (self.y_max + self.y_min)) / (self.y_max - self.y_min)
        
        x_factor = 1.0 - xi**2
        y_factor = 1.0 - eta**2
        return x_factor * y_factor

    def forward(self, xy):
        # Chuẩn hóa đầu vào của mạng Nơ-ron về [-1, 1]
        xi = (2.0 * xy[:, 0:1] - (self.x_max + self.x_min)) / (self.x_max - self.x_min)
        eta = (2.0 * xy[:, 1:2] - (self.y_max + self.y_min)) / (self.y_max - self.y_min)
        xy_normalized = torch.cat([xi, eta], dim=1)
        
        raw_output = self.network(xy_normalized)
        
        A_z_star = raw_output * self.boundary_factor(xy)
        return A_z_star
