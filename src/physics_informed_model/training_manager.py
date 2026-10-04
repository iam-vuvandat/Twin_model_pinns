import torch
import torch.optim as optim

class TrainingManager:
    # 1. THÊM target_loss VÀO HÀM KHỞI TẠO
    def __init__(self, model, pde_evaluator, lr_adam=1e-3, target_loss=1e-3):
        self.model = model
        self.pde_evaluator = pde_evaluator
        self.target_loss = target_loss
        
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

    def compute_loss(self, points_tensor, reluctivity_tensor, current_density_z_tensor, coercive_field_x_tensor, coercive_field_y_tensor):
        A_z_star = self.model(points_tensor)
        
        residual_star = self.pde_evaluator.compute_residual(
            xy=points_tensor,
            A_z_star=A_z_star,
            nu=reluctivity_tensor,
            J_z=current_density_z_tensor,
            H_cx=coercive_field_x_tensor,
            H_cy=coercive_field_y_tensor
        )
        
        loss_pde = torch.mean(residual_star**2)
        return loss_pde

    def train_adam(self, epochs, points_tensor, reluctivity_tensor, current_density_z_tensor, coercive_field_x_tensor, coercive_field_y_tensor):
        self.model.train()
        best_loss = float('inf')
        best_model_state = {key: value.cpu().clone() for key, value in self.model.state_dict().items()}
        
        scheduler_adam = optim.lr_scheduler.CosineAnnealingLR(self.optimizer_adam, T_max=epochs, eta_min=1e-6)
        
        for epoch in range(epochs):
            self.optimizer_adam.zero_grad()
            
            loss = self.compute_loss(
                points_tensor, reluctivity_tensor, 
                current_density_z_tensor, coercive_field_x_tensor, coercive_field_y_tensor
            )
            
            if torch.isnan(loss) or loss.item() > 1.5 * best_loss:
                self.model.load_state_dict(best_model_state)
                for param_group in self.optimizer_adam.param_groups:
                    param_group['lr'] *= 0.8
                continue
                
            loss.backward(retain_graph=True)
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            self.optimizer_adam.step()
            scheduler_adam.step()
            
            current_loss_value = loss.item()
            
            # 2. SỬ DỤNG THUỘC TÍNH CỦA LỚP ĐỂ KIỂM TRA
            if self.target_loss > 0 and current_loss_value < self.target_loss:
                print(f"Adam Epoch {epoch + 1}: Đạt ngưỡng loss mục tiêu < {self.target_loss} ({current_loss_value:.6e}). KẾT THÚC ADAM SỚM!")
                break
            
            if current_loss_value < best_loss:
                best_loss = current_loss_value
                best_model_state = {key: value.cpu().clone() for key, value in self.model.state_dict().items()}
            
            if (epoch + 1) % 100 == 0:
                current_lr = self.optimizer_adam.param_groups[0]['lr']
                print(f"Adam Epoch {epoch + 1}: Loss = {current_loss_value:.6e} | LR = {current_lr:.3e}")

    def train_lbfgs(self, epochs, points_tensor, reluctivity_tensor, current_density_z_tensor, coercive_field_x_tensor, coercive_field_y_tensor):
        self.model.train()
        for epoch in range(epochs):
            def closure():
                self.optimizer_lbfgs.zero_grad()
                loss = self.compute_loss(
                    points_tensor, reluctivity_tensor, 
                    current_density_z_tensor, coercive_field_x_tensor, coercive_field_y_tensor
                )
                loss.backward(retain_graph=True)
                return loss
            
            loss_val = self.optimizer_lbfgs.step(closure)
            print(f"L-BFGS Epoch {epoch + 1}: Loss = {loss_val.item():.6e}")
            
            # 3. SỬ DỤNG THUỘC TÍNH CỦA LỚP ĐỂ KIỂM TRA
            if self.target_loss > 0 and loss_val.item() < self.target_loss:
                print(f"L-BFGS Epoch {epoch + 1}: Đạt ngưỡng loss mục tiêu < {self.target_loss} ({loss_val.item():.6e}). KẾT THÚC L-BFGS SỚM!")
                break
