import torch
import torch.nn as nn

class PINNArchitecture(nn.Module):
    def __init__(self, input_dim=2, hidden_layers=4, hidden_neurons=50, output_dim=1):
        super().__init__()
        
        layers = []
        layers.append(nn.Linear(input_dim, hidden_neurons))
        layers.append(nn.Tanh())
        
        for _ in range(hidden_layers - 1):
            layers.append(nn.Linear(hidden_neurons, hidden_neurons))
            layers.append(nn.Tanh())
            
        layers.append(nn.Linear(hidden_neurons, output_dim))
        
        self.network = nn.Sequential(*layers)

    def forward(self, xy, sdf_boundary):
        raw_output = self.network(xy)
        
        A_z = raw_output * sdf_boundary
        return A_z
