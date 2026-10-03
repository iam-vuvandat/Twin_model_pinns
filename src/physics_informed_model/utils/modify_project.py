import os

def update_source_code_only():
    base_directory = os.path.dirname(os.path.abspath(__file__))
    project_root_directory = os.path.abspath(os.path.join(base_directory, '..'))
    
    # 1. Cập nhật tệp electro_magnetic_pinn.py
    electro_magnetic_path = os.path.join(project_root_directory, 'electro_magnetic_pinn.py')
    electro_magnetic_code = """import torch
import torch.nn as nn
from pinn_architecture import PINNArchitecture
from training_manager import TrainingManager
from physics_domain.physical_equations.maxwell_pde_loss import MaxwellPDELoss

class ElectroMagneticPINN:
    def __init__(self, geometry_engine_instance, collocation_sampler_instance, hidden_layers=4, hidden_neurons=50, activation_function=nn.SiLU()):
        self.geometry_engine_instance = geometry_engine_instance
        self.collocation_sampler_instance = collocation_sampler_instance
        
        self.L0 = self.collocation_sampler_instance.x_maximum
        self.H0 = 800000.0
        self.nu0 = self.geometry_engine_instance.vacuum_reluctivity
        self.A0 = (self.H0 * self.L0) / self.nu0
        
        self.pinn_architecture_instance = PINNArchitecture(
            domain_scale=self.L0,
            hidden_layers=hidden_layers,
            hidden_neurons=hidden_neurons,
            activation_function=activation_function
        )
        self.maxwell_pde_loss_instance = MaxwellPDELoss(L0=self.L0, H0=self.H0, nu0=self.nu0)
        
        self.training_manager_instance = TrainingManager(
            model=self.pinn_architecture_instance,
            pde_evaluator=self.maxwell_pde_loss_instance
        )

    def execute_training_process(self, number_of_uniform_points, number_of_interface_points, distance_threshold, epochs_adam, epochs_lbfgs):
        points_tensor = self.collocation_sampler_instance.generate_combined_points_tensor(
            geometry_object=self.geometry_engine_instance,
            number_of_uniform_points=number_of_uniform_points,
            number_of_interface_points=number_of_interface_points,
            distance_threshold=distance_threshold
        )
        
        physical_properties_dictionary = self.geometry_engine_instance.evaluate_global_physical_properties(points_tensor)
        
        print(f"--- Standard Adam Training ({epochs_adam} Epochs) ---")
        self.training_manager_instance.train_adam(
            epochs=epochs_adam,
            points_tensor=points_tensor,
            reluctivity_tensor=physical_properties_dictionary["reluctivity"],
            current_density_z_tensor=physical_properties_dictionary["current_density_z"],
            coercive_field_x_tensor=physical_properties_dictionary["coercive_field_x"],
            coercive_field_y_tensor=physical_properties_dictionary["coercive_field_y"]
        )
        
        print(f"--- L-BFGS Refinement ({epochs_lbfgs} Epochs) ---")
        self.training_manager_instance.train_lbfgs(
            epochs=epochs_lbfgs, 
            points_tensor=points_tensor, 
            reluctivity_tensor=physical_properties_dictionary["reluctivity"], 
            current_density_z_tensor=physical_properties_dictionary["current_density_z"], 
            coercive_field_x_tensor=physical_properties_dictionary["coercive_field_x"], 
            coercive_field_y_tensor=physical_properties_dictionary["coercive_field_y"]
        )

    def predict_magnetic_vector_potential(self, points_tensor):
        self.pinn_architecture_instance.eval()
        with torch.no_grad():
            A_z_star = self.pinn_architecture_instance(points_tensor)
        return A_z_star * self.A0

    def evaluate_fields(self, points_tensor):
        self.pinn_architecture_instance.eval()
        points_tensor.requires_grad_(True)
        
        A_z_star = self.pinn_architecture_instance(points_tensor)
        A_z_phys = A_z_star * self.A0
        
        grad_A = torch.autograd.grad(
            outputs=A_z_phys,
            inputs=points_tensor,
            grad_outputs=torch.ones_like(A_z_phys),
            create_graph=False,
            retain_graph=False
        )[0]
        
        B_x = grad_A[:, 1:2]
        B_y = -grad_A[:, 0:1]
        
        return A_z_phys.detach(), B_x.detach(), B_y.detach()
"""

    with open(electro_magnetic_path, 'w', encoding='utf-8') as f:
        f.write(electro_magnetic_code)

    # 2. Cập nhật tệp pinn_architecture.py (Cần thiết để nhận activation_function)
    pinn_arch_path = os.path.join(project_root_directory, 'pinn_architecture.py')
    pinn_arch_code = """import torch
import torch.nn as nn

class PINNArchitecture(nn.Module):
    def __init__(self, input_dim=2, hidden_layers=4, hidden_neurons=50, output_dim=1, domain_scale=0.05, activation_function=nn.SiLU()):
        super().__init__()
        self.domain_scale = domain_scale
        
        layers = []
        layers.append(nn.Linear(input_dim, hidden_neurons))
        layers.append(activation_function)
        
        for _ in range(hidden_layers - 1):
            layers.append(nn.Linear(hidden_neurons, hidden_neurons))
            layers.append(activation_function)
            
        layers.append(nn.Linear(hidden_neurons, output_dim))
        
        self.network = nn.Sequential(*layers)
        self._initialize_weights()

    def _initialize_weights(self):
        for module in self.network:
            if isinstance(module, nn.Linear):
                nn.init.xavier_normal_(module.weight)
                nn.init.zeros_(module.bias)

    def boundary_factor(self, xy):
        x_factor = 1.0 - (xy[:, 0:1] / self.domain_scale)**2
        y_factor = 1.0 - (xy[:, 1:2] / self.domain_scale)**2
        return x_factor * y_factor

    def forward(self, xy):
        xy_normalized = xy / self.domain_scale
        raw_output = self.network(xy_normalized)
        
        A_z_star = raw_output * self.boundary_factor(xy)
        return A_z_star
"""
    with open(pinn_arch_path, 'w', encoding='utf-8') as f:
        f.write(pinn_arch_code)

    print("Đã cập nhật xong tệp electro_magnetic_pinn.py và pinn_architecture.py thành công!")

if __name__ == "__main__":
    update_source_code_only()