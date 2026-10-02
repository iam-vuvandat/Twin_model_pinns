import torch
import torch.optim as optim

class TrainingManager:
    def __init__(self, model, pde_evaluator, material_mapping, lr_adam=1e-3):
        self.model = model
        self.pde_evaluator = pde_evaluator
        self.material_mapping = material_mapping
        
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

    def compute_loss(self, xy, sdf_boundary, iron_mask, magnet_mask, slot_masks_dict, slot_current_dict, H_cx, H_cy):
        A_z = self.model(xy, sdf_boundary)
        
        nu = self.material_mapping.get_reluctivity(iron_mask, magnet_mask)
        J_z = self.material_mapping.get_current_density(xy, slot_masks_dict, slot_current_dict)
        
        residual = self.pde_evaluator.compute_residual(xy, A_z, nu, J_z, H_cx, H_cy)
        
        loss_pde = torch.mean(residual**2)
        return loss_pde

    def train_adam(self, epochs, xy, sdf_boundary, iron_mask, magnet_mask, slot_masks_dict, slot_current_dict, H_cx, H_cy):
        self.model.train()
        for epoch in range(epochs):
            self.optimizer_adam.zero_grad()
            
            loss = self.compute_loss(
                xy, sdf_boundary, iron_mask, magnet_mask, 
                slot_masks_dict, slot_current_dict, H_cx, H_cy
            )
            
            loss.backward(retain_graph=True)
            self.optimizer_adam.step()
            
            if (epoch + 1) % 100 == 0:
                print(f"Adam Epoch {epoch + 1}: Loss = {loss.item():.6e}")

    def train_lbfgs(self, epochs, xy, sdf_boundary, iron_mask, magnet_mask, slot_masks_dict, slot_current_dict, H_cx, H_cy):
        self.model.train()
        for epoch in range(epochs):
            def closure():
                self.optimizer_lbfgs.zero_grad()
                loss = self.compute_loss(
                    xy, sdf_boundary, iron_mask, magnet_mask, 
                    slot_masks_dict, slot_current_dict, H_cx, H_cy
                )
                loss.backward(retain_graph=True)
                return loss
            
            # 2. SỬA LỖI HIỆU SUẤT L-BFGS: Không gọi closure() lần thứ 2
            loss_val = self.optimizer_lbfgs.step(closure)
            print(f"L-BFGS Epoch {epoch + 1}: Loss = {loss_val.item():.6e}")
