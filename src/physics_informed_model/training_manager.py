import torch
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
