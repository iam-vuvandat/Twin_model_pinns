import torch
import torch.optim as optim

class TrainingManager:
    def __init__(self, model, pde_evaluator, lr_adam=1e-3):
        self.model = model
        self.pde_evaluator = pde_evaluator
        
        self.optimizer_adam = optim.Adam(self.model.parameters(), lr=lr_adam)
        
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

    def compute_loss(self, points_tensor, signed_distance_field_tensor, reluctivity_tensor, current_density_z_tensor, coercive_field_x_tensor, coercive_field_y_tensor):
        magnetic_vector_potential_z_tensor = self.model(points_tensor, signed_distance_field_tensor)
        
        residual = self.pde_evaluator.compute_residual(
            xy=points_tensor,
            A_z=magnetic_vector_potential_z_tensor,
            nu=reluctivity_tensor,
            J_z=current_density_z_tensor,
            H_cx=coercive_field_x_tensor,
            H_cy=coercive_field_y_tensor
        )
        
        loss_pde = torch.mean(residual**2)
        return loss_pde

    def train_adam(self, epochs, points_tensor, signed_distance_field_tensor, reluctivity_tensor, current_density_z_tensor, coercive_field_x_tensor, coercive_field_y_tensor):
        self.model.train()
        for epoch in range(epochs):
            self.optimizer_adam.zero_grad()
            
            loss = self.compute_loss(
                points_tensor, signed_distance_field_tensor, reluctivity_tensor, 
                current_density_z_tensor, coercive_field_x_tensor, coercive_field_y_tensor
            )
            
            loss.backward(retain_graph=True)
            self.optimizer_adam.step()
            
            if (epoch + 1) % 100 == 0:
                print(f"Adam Epoch {epoch + 1}: Loss = {loss.item():.6e}")

    def train_lbfgs(self, epochs, points_tensor, signed_distance_field_tensor, reluctivity_tensor, current_density_z_tensor, coercive_field_x_tensor, coercive_field_y_tensor):
        self.model.train()
        for epoch in range(epochs):
            def closure():
                self.optimizer_lbfgs.zero_grad()
                loss = self.compute_loss(
                    points_tensor, signed_distance_field_tensor, reluctivity_tensor, 
                    current_density_z_tensor, coercive_field_x_tensor, coercive_field_y_tensor
                )
                loss.backward(retain_graph=True)
                return loss
            
            self.optimizer_lbfgs.step(closure)
            
            loss_val = closure()
            print(f"L-BFGS Epoch {epoch + 1}: Loss = {loss_val.item():.6e}")
