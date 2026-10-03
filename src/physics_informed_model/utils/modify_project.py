import os

def apply_critical_bug_fixes():
    base_directory = os.path.dirname(os.path.abspath(__file__))
    project_root_directory = os.path.abspath(os.path.join(base_directory, '..'))
    
    training_manager_path = os.path.join(project_root_directory, 'training_manager.py')
    maxwell_pde_loss_path = os.path.join(project_root_directory, 'physics_domain', 'physical_equations', 'maxwell_pde_loss.py')

    training_manager_source_code = """import torch
import torch.optim as optim
import copy

class TrainingManager:
    def __init__(self, model, pde_evaluator, geometry_engine_instance, lr_adam=1e-3):
        self.model = model
        self.pde_evaluator = pde_evaluator
        self.geometry_engine_instance = geometry_engine_instance
        self.base_lr_adam = lr_adam
        
        self.loss_history = []
        self.best_model_state = None
        self.last_model_state = None
        
        self.optimizer_adam = optim.Adam(self.model.parameters(), lr=self.base_lr_adam)
        self.optimizer_lbfgs = optim.LBFGS(
            self.model.parameters(),
            lr=1.0,
            max_iter=50,
            max_eval=50,
            tolerance_grad=1e-7,
            tolerance_change=1e-9,
            history_size=100,
            line_search_fn="strong_wolfe"
        )

    def compute_loss(self, points_tensor, alpha=1.0):
        phys_props = self.geometry_engine_instance.evaluate_global_physical_properties(points_tensor)
        nu = phys_props["reluctivity"]
        J_z = phys_props["current_density_z"] * alpha
        H_cx = phys_props["coercive_field_x"] * alpha
        H_cy = phys_props["coercive_field_y"] * alpha

        A_z_star = self.model(points_tensor)
        
        residual_star = self.pde_evaluator.compute_residual(
            xy=points_tensor,
            A_z_star=A_z_star,
            nu=nu,
            J_z=J_z,
            H_cx=H_cx,
            H_cy=H_cy
        )
        
        loss_pde = torch.mean(residual_star**2)
        return loss_pde

    def train_adam(self, epochs, points_tensor, alpha):
        self.model.train()
        best_loss = float('inf')
        
        for param_group in self.optimizer_adam.param_groups:
            param_group['initial_lr'] = self.base_lr_adam
            param_group['lr'] = self.base_lr_adam
            
        if self.best_model_state is None:
            self.best_model_state = copy.deepcopy(self.model.state_dict())
        
        scheduler_adam = optim.lr_scheduler.CosineAnnealingLR(self.optimizer_adam, T_max=epochs, eta_min=1e-6)
        
        for epoch in range(epochs):
            self.optimizer_adam.zero_grad()
            
            loss = self.compute_loss(points_tensor, alpha)
            
            if torch.isnan(loss) or loss.item() > 10.0 * best_loss:
                self.model.load_state_dict(self.best_model_state)
                for param_group in self.optimizer_adam.param_groups:
                    param_group['lr'] *= 0.8
                continue
                
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            self.optimizer_adam.step()
            scheduler_adam.step()
            
            current_loss_value = loss.item()
            self.loss_history.append(current_loss_value)
            
            if current_loss_value < best_loss:
                best_loss = current_loss_value
                self.best_model_state = copy.deepcopy(self.model.state_dict())
            
            if (epoch + 1) % 100 == 0:
                current_lr = self.optimizer_adam.param_groups[0]['lr']
                print(f"Adam Epoch {epoch + 1}: Loss = {current_loss_value:.6e} | LR = {current_lr:.3e}")
                
        self.last_model_state = copy.deepcopy(self.model.state_dict())

    def train_lbfgs(self, epochs, points_tensor, alpha):
        self.model.train()
        for epoch in range(epochs):
            def closure():
                self.optimizer_lbfgs.zero_grad()
                loss = self.compute_loss(points_tensor, alpha)
                loss.backward()
                return loss
            
            loss_val = self.optimizer_lbfgs.step(closure)
            current_loss_value = loss_val.item()
            self.loss_history.append(current_loss_value)
            self.last_model_state = copy.deepcopy(self.model.state_dict())
            
            print(f"L-BFGS Epoch {epoch + 1}: Loss = {current_loss_value:.6e}")
"""

    maxwell_pde_loss_source_code = """import torch

class MaxwellPDELoss:
    def __init__(self, L0=0.05, H0=800000.0, nu0=795774.715459):
        self.L0 = L0
        self.H0 = H0
        self.nu0 = nu0

    def compute_residual(self, xy, A_z_star, nu, J_z, H_cx, H_cy):
        nu_star = nu / self.nu0
        H_cx_star = H_cx / self.H0
        H_cy_star = H_cy / self.H0
        J_z_star = J_z / (self.H0 / self.L0)
        
        grad_A_star = torch.autograd.grad(
            outputs=A_z_star,
            inputs=xy,
            grad_outputs=torch.ones_like(A_z_star),
            create_graph=True,
            retain_graph=True
        )[0]
        
        dAz_star_dx_star = grad_A_star[:, 0:1] * self.L0
        dAz_star_dy_star = grad_A_star[:, 1:2] * self.L0
        
        H_x_star = nu_star * dAz_star_dy_star - H_cx_star
        H_y_star = -nu_star * dAz_star_dx_star - H_cy_star
        
        grad_Hx_star = torch.autograd.grad(
            outputs=H_x_star,
            inputs=xy,
            grad_outputs=torch.ones_like(H_x_star),
            create_graph=True,
            retain_graph=True
        )[0]
        dHx_star_dy_star = grad_Hx_star[:, 1:2] * self.L0
        
        grad_Hy_star = torch.autograd.grad(
            outputs=H_y_star,
            inputs=xy,
            grad_outputs=torch.ones_like(H_y_star),
            create_graph=True,
            retain_graph=True
        )[0]
        dHy_star_dx_star = grad_Hy_star[:, 0:1] * self.L0
        
        residual_star = dHy_star_dx_star - dHx_star_dy_star - J_z_star
        return residual_star
"""

    with open(training_manager_path, 'w', encoding='utf-8') as f:
        f.write(training_manager_source_code)
    
    with open(maxwell_pde_loss_path, 'w', encoding='utf-8') as f:
        f.write(maxwell_pde_loss_source_code)
        
    print("Đã vá thành công các lỗi về Autograd và cấu trúc giải phóng bộ nhớ.")

if __name__ == '__main__':
    apply_critical_bug_fixes()