import torch
import torch.nn as nn
import numpy as np

class PINNArchitecture(nn.Module):
    def __init__(self, input_dim=2, hidden_layers=4, hidden_neurons=64, output_dim=1, domain_scale=0.05, activation_function=nn.SiLU(), use_fourier=True, fourier_features=64, fourier_scale=1.0):
        super().__init__()
        self.domain_scale = domain_scale
        self.use_fourier = use_fourier
        
        # 1. TÍCH HỢP FOURIER FEATURES (Khắc phục thiên lệch tần số)
        if self.use_fourier:
            # Ma trận ngẫu nhiên B (không cập nhật trọng số)
            self.B = nn.Parameter(torch.randn(input_dim, fourier_features) * fourier_scale, requires_grad=False)
            network_input_dim = fourier_features * 2  # Gấp đôi vì dùng cả Sin và Cos
        else:
            network_input_dim = input_dim
            
        # 2. KHỐI DÙNG CHUNG (Backbone)
        common_layers = []
        common_layers.append(nn.Linear(network_input_dim, hidden_neurons))
        common_layers.append(activation_function)
        
        # Để lại 1 lớp cuối cùng cho các nhánh chuyên gia
        for _ in range(max(1, hidden_layers - 1)):
            common_layers.append(nn.Linear(hidden_neurons, hidden_neurons))
            common_layers.append(activation_function)
            
        self.common_block = nn.Sequential(*common_layers)
        
        # 3. BỐN NHÁNH CHUYÊN GIA SONG SONG
        self.branch_air = nn.Linear(hidden_neurons, output_dim)
        self.branch_magnet = nn.Linear(hidden_neurons, output_dim)
        self.branch_iron = nn.Linear(hidden_neurons, output_dim)
        self.branch_copper = nn.Linear(hidden_neurons, output_dim)
        
        self._initialize_weights()

    def _initialize_weights(self):
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_normal_(module.weight)
                nn.init.zeros_(module.bias)

    def boundary_factor(self, xy):
        x_factor = 1.0 - (xy[:, 0:1] / self.domain_scale)**2
        y_factor = 1.0 - (xy[:, 1:2] / self.domain_scale)**2
        return x_factor * y_factor

    def forward(self, xy, masks_dict=None):
        xy_normalized = xy / self.domain_scale
        
        # Ánh xạ Fourier
        if self.use_fourier:
            x_proj = (2.0 * np.pi * xy_normalized) @ self.B
            xy_input = torch.cat([torch.sin(x_proj), torch.cos(x_proj)], dim=-1)
        else:
            xy_input = xy_normalized
            
        # Đi qua khối chung
        z = self.common_block(xy_input)
        
        # 4 nhánh tính toán song song
        f_air = self.branch_air(z)
        f_mag = self.branch_magnet(z)
        f_iron = self.branch_iron(z)
        f_copper = self.branch_copper(z)
        
        # Trộn nghiệm bằng mặt nạ
        if masks_dict is not None:
            m_mag = 0.0
            m_iron = 0.0
            m_copper = 0.0
            
            # Lọc linh hoạt theo tên vật liệu chứa từ khóa (VD: 'top_magnet' -> magnet)
            for k, v in masks_dict.items():
                k_lower = k.lower()
                if 'magnet' in k_lower:
                    m_mag = m_mag + v
                elif 'iron' in k_lower:
                    m_iron = m_iron + v
                elif 'copper' in k_lower:
                    m_copper = m_copper + v
            
            # Đảm bảo mask là Tensor và không vượt quá 1.0
            def format_mask(m):
                if isinstance(m, float): return torch.tensor(m, device=xy.device)
                return torch.clamp(m, 0.0, 1.0)
                
            m_mag = format_mask(m_mag)
            m_iron = format_mask(m_iron)
            m_copper = format_mask(m_copper)
            
            # Tính mask không khí (phần còn trống)
            m_air = 1.0 - torch.clamp(m_mag + m_iron + m_copper, 0.0, 1.0)
            
            # Khóa Đạo hàm (Gradient Masking)
            raw_output = (f_air * m_air) + (f_mag * m_mag) + (f_iron * m_iron) + (f_copper * m_copper)
        else:
            # Fallback nếu không truyền mask_dict
            raw_output = f_air + f_mag + f_iron + f_copper
            
        A_z_star = raw_output * self.boundary_factor(xy)
        return A_z_star
