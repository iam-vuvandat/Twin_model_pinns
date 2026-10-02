import torch
import torch.nn as nn

class PINNArchitecture(nn.Module):
    # [CẬP NHẬT]: Thêm domain_scale = 0.05
    def __init__(self, input_dim=2, hidden_layers=4, hidden_neurons=50, output_dim=1, domain_scale=0.05):
        super().__init__()
        self.domain_scale = domain_scale
        
        layers = []
        layers.append(nn.Linear(input_dim, hidden_neurons))
        layers.append(nn.SiLU())
        
        for _ in range(hidden_layers - 1):
            layers.append(nn.Linear(hidden_neurons, hidden_neurons))
            layers.append(nn.SiLU())
            
        layers.append(nn.Linear(hidden_neurons, output_dim))
        
        self.network = nn.Sequential(*layers)
        self._initialize_weights()

    def _initialize_weights(self):
        for module in self.network:
            if isinstance(module, nn.Linear):
                nn.init.xavier_normal_(module.weight)
                nn.init.zeros_(module.bias)

    def forward(self, xy, sdf_boundary):
        # [CẬP NHẬT CỐT LÕI]: Chuẩn hóa tọa độ. Các trọng số N(0,1) không thể xử lý tọa độ quá nhỏ (0.01)
        xy_normalized = xy / self.domain_scale
        raw_output = self.network(xy_normalized)
        
        A_z = raw_output * sdf_boundary
        return A_z
