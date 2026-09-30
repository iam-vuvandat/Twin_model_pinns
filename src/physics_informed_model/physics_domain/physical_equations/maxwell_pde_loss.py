import torch

class MaxwellPDELoss:
    def __init__(self):
        pass

    def compute_residual(self, xy, A_z, nu, J_z, H_cx, H_cy):
        grad_A = torch.autograd.grad(
            outputs=A_z,
            inputs=xy,
            grad_outputs=torch.ones_like(A_z),
            create_graph=True,
            retain_graph=True
        )[0]
        
        dAz_dx = grad_A[:, 0:1]
        dAz_dy = grad_A[:, 1:2]
        
        H_x = nu * dAz_dy - H_cx
        H_y = -nu * dAz_dx - H_cy
        
        grad_Hx = torch.autograd.grad(
            outputs=H_x,
            inputs=xy,
            grad_outputs=torch.ones_like(H_x),
            create_graph=True,
            retain_graph=True
        )[0]
        dHx_dy = grad_Hx[:, 1:2]
        
        grad_Hy = torch.autograd.grad(
            outputs=H_y,
            inputs=xy,
            grad_outputs=torch.ones_like(H_y),
            create_graph=True,
            retain_graph=True
        )[0]
        dHy_dx = grad_Hy[:, 0:1]
        
        residual = dHy_dx - dHx_dy - J_z
        return residual