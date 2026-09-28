import math
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import matplotlib.pyplot as plt

SEED = 42
torch.manual_seed(SEED)
np.random.seed(SEED)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
DTYPE = torch.float32

if torch.cuda.is_available():
    torch.backends.cudnn.benchmark = True
    print(f"[DEBUG] Hardware using for training: GPU ({torch.cuda.get_device_name(0)})")
else:
    print("[DEBUG] Hardware using for training: CPU")

MU0 = 4.0 * math.pi * 1.0e-7
MUR_IRON = 1000.0
L0 = 1.0
M0 = 1.0e6
A0 = MU0 * M0 * L0
B0 = MU0 * M0

LENGTH_X = 0.30
WIDTH_Y = 0.12
STEEPNESS = 60.0

MAGNET_OFFSET_X = 1.5 * LENGTH_X

SPAN_X = MAGNET_OFFSET_X + LENGTH_X
YOKE_LENGTH_X = 1.10 * SPAN_X
YOKE_WIDTH_Y = WIDTH_Y
YOKE_OFFSET_Y = -(2.0 * WIDTH_Y)

class MagnetizationSource:
    def __init__(self, length_x=LENGTH_X, width_y=WIDTH_Y, offset_x=MAGNET_OFFSET_X, steepness=STEEPNESS):
        self.lx = float(length_x)
        self.wy = float(width_y)
        self.offset_x = float(offset_x)
        self.k = float(steepness)

    def dimensionless(self, xy):
        x = xy[:, 0:1]
        y = xy[:, 1:2]
        
        sig_x1 = torch.sigmoid(self.k * (x + self.offset_x + self.lx)) - torch.sigmoid(self.k * (x + self.offset_x - self.lx))
        sig_x2 = torch.sigmoid(self.k * (x - self.offset_x + self.lx)) - torch.sigmoid(self.k * (x - self.offset_x - self.lx))
        
        sig_y = torch.sigmoid(self.k * (y + self.wy)) - torch.sigmoid(self.k * (y - self.wy))
        
        return (-sig_x1 + sig_x2) * sig_y

    def physical(self, xy):
        return M0 * self.dimensionless(xy)

    def dmx_dy_dimensionless(self, xy):
        x = xy[:, 0:1]
        y = xy[:, 1:2]
        
        sig_x1 = torch.sigmoid(self.k * (x + self.offset_x + self.lx)) - torch.sigmoid(self.k * (x + self.offset_x - self.lx))
        sig_x2 = torch.sigmoid(self.k * (x - self.offset_x + self.lx)) - torch.sigmoid(self.k * (x - self.offset_x - self.lx))
        
        s_y_plus = torch.sigmoid(self.k * (y + self.wy))
        s_y_minus = torch.sigmoid(self.k * (y - self.wy))
        ds_y = self.k * s_y_plus * (1.0 - s_y_plus) - self.k * s_y_minus * (1.0 - s_y_minus)
        
        return (-sig_x1 + sig_x2) * ds_y

    def dmx_dy_physical(self, xy):
        return (M0 / L0) * self.dmx_dy_dimensionless(xy)

class MaterialPermeability:
    def __init__(self, yoke_lx=YOKE_LENGTH_X, yoke_wy=YOKE_WIDTH_Y, yoke_offset_y=YOKE_OFFSET_Y, mur=MUR_IRON, steepness=STEEPNESS):
        self.lx = float(yoke_lx)
        self.wy = float(yoke_wy)
        self.y0 = float(yoke_offset_y)
        self.mur = float(mur)
        self.k = float(steepness)
        self.nu_air = 1.0
        self.nu_iron = 1.0 / self.mur

    def nu_r_dimensionless(self, xy):
        x = xy[:, 0:1]
        y = xy[:, 1:2]
        sig_x = torch.sigmoid(self.k * (x + self.lx)) - torch.sigmoid(self.k * (x - self.lx))
        sig_y = torch.sigmoid(self.k * (y - self.y0 + self.wy)) - torch.sigmoid(self.k * (y - self.y0 - self.wy))
        mask_iron = sig_x * sig_y
        return self.nu_air + (self.nu_iron - self.nu_air) * mask_iron

    def mu_r_dimensionless(self, xy):
        return 1.0 / self.nu_r_dimensionless(xy)

class BoundaryCondition:
    def __init__(self, x_min=-1.0, x_max=1.0, y_min=-1.0, y_max=1.0, num_points=250):
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.num_points = num_points

    def sample_points(self, device=DEVICE):
        x_bottom = torch.empty(self.num_points, 1, device=device, dtype=DTYPE).uniform_(self.x_min, self.x_max)
        y_bottom = torch.full((self.num_points, 1), self.y_min, device=device, dtype=DTYPE)
        
        x_top = torch.empty(self.num_points, 1, device=device, dtype=DTYPE).uniform_(self.x_min, self.x_max)
        y_top = torch.full((self.num_points, 1), self.y_max, device=device, dtype=DTYPE)
        
        x_left = torch.full((self.num_points, 1), self.x_min, device=device, dtype=DTYPE)
        y_left = torch.empty(self.num_points, 1, device=device, dtype=DTYPE).uniform_(self.y_min, self.y_max)
        
        x_right = torch.full((self.num_points, 1), self.x_max, device=device, dtype=DTYPE)
        y_right = torch.empty(self.num_points, 1, device=device, dtype=DTYPE).uniform_(self.y_min, self.y_max)
        
        bottom = torch.cat([x_bottom, y_bottom], dim=1)
        top = torch.cat([x_top, y_top], dim=1)
        left = torch.cat([x_left, y_left], dim=1)
        right = torch.cat([x_right, y_right], dim=1)
        
        return torch.cat([bottom, top, left, right], dim=0)

    @staticmethod
    def loss(model, points):
        Az = model(points)
        return torch.mean(Az**2)

    @staticmethod
    def max_error(model, points):
        with torch.no_grad():
            Az = model(points)
        return torch.max(torch.abs(Az)).item()

class MagneticPINN(nn.Module):
    def __init__(self, hidden_layers=6, neurons=128, hard_boundary=True):
        super().__init__()
        self.hard_boundary = hard_boundary
        
        layers = [nn.Linear(2, neurons), nn.Tanh()]
        for _ in range(hidden_layers - 1):
            layers += [nn.Linear(neurons, neurons), nn.Tanh()]
        layers.append(nn.Linear(neurons, 1))
        
        self.net = nn.Sequential(*layers)
        
        for module in self.net:
            if isinstance(module, nn.Linear):
                nn.init.xavier_normal_(module.weight)
                nn.init.zeros_(module.bias)

    def forward(self, xy):
        raw = self.net(xy)
        if self.hard_boundary:
            x = xy[:, 0:1]
            y = xy[:, 1:2]
            boundary_factor = (1.0 - x**2) * (1.0 - y**2)
            return boundary_factor * raw
        return raw

def sample_collocation_points(num_points, x_min=-1.0, x_max=1.0, y_min=-1.0, y_max=1.0, device=DEVICE, engine=None):
    if engine is None:
        engine = torch.quasirandom.SobolEngine(dimension=2, scramble=True)
    uv = engine.draw(num_points).to(device=device, dtype=DTYPE)
    
    x = x_min + (x_max - x_min) * uv[:, 0:1]
    y = y_min + (y_max - y_min) * uv[:, 1:2]
    
    xy = torch.cat([x, y], dim=1)
    xy.requires_grad_(True)
    return xy

def compute_pde_loss(model, xy_collocation, source, material):
    Az_star = model(xy_collocation)
    
    grads = torch.autograd.grad(
        outputs=Az_star, inputs=xy_collocation,
        grad_outputs=torch.ones_like(Az_star), create_graph=True
    )[0]
    
    dAz_dx_star = grads[:, 0:1]
    dAz_dy_star = grads[:, 1:2]
    
    nu_r = material.nu_r_dimensionless(xy_collocation)
    
    flux_x = nu_r * dAz_dx_star
    flux_y = nu_r * dAz_dy_star
    
    div_flux_x = torch.autograd.grad(
        outputs=flux_x, inputs=xy_collocation,
        grad_outputs=torch.ones_like(flux_x), create_graph=True, retain_graph=True
    )[0][:, 0:1]
    
    div_flux_y = torch.autograd.grad(
        outputs=flux_y, inputs=xy_collocation,
        grad_outputs=torch.ones_like(flux_y), create_graph=True
    )[0][:, 1:2]
    
    dmx_dy_star = source.dmx_dy_dimensionless(xy_collocation)
    
    residual = div_flux_x + div_flux_y - dmx_dy_star
    loss_pde = torch.mean(residual**2)
    return loss_pde, residual

def evaluate_fields(model, resolution=160, device=DEVICE):
    model.eval()
    
    x_star = np.linspace(-1.0, 1.0, resolution)
    y_star = np.linspace(-1.0, 1.0, resolution)
    X_star, Y_star = np.meshgrid(x_star, y_star)
    
    xy_np = np.column_stack((X_star.ravel(), Y_star.ravel())).astype(np.float32)
    xy = torch.tensor(xy_np, device=device, dtype=DTYPE, requires_grad=True)
    
    Az_star = model(xy)
    
    grads = torch.autograd.grad(
        outputs=Az_star, inputs=xy,
        grad_outputs=torch.ones_like(Az_star), create_graph=False
    )[0]
    
    dAz_dx_star = grads[:, 0:1]
    dAz_dy_star = grads[:, 1:2]
    
    Az = (A0 * Az_star).detach().cpu().numpy().reshape(X_star.shape)
    Bx = (B0 * dAz_dy_star).detach().cpu().numpy().reshape(X_star.shape)
    By = (-B0 * dAz_dx_star).detach().cpu().numpy().reshape(X_star.shape)
    Bmag = np.sqrt(Bx**2 + By**2)
    
    source = MagnetizationSource()
    material = MaterialPermeability()
    xy_detached = xy.detach()
    
    with torch.no_grad():
        Mx = source.physical(xy_detached).cpu().numpy().reshape(X_star.shape)
        dMx_dy = source.dmx_dy_physical(xy_detached).cpu().numpy().reshape(X_star.shape)
        Mur = material.mu_r_dimensionless(xy_detached).cpu().numpy().reshape(X_star.shape)
        
    X = L0 * X_star
    Y = L0 * Y_star
    model.train()
    
    return {"X": X, "Y": Y, "Az": Az, "Bx": Bx, "By": By, "Bmag": Bmag, "Mx": Mx, "dMx_dy": dMx_dy, "Mur": Mur}

def train_pinn(epochs=6000, num_collocation=12000, hidden_layers=6, neurons=128, learning_rate=1.0e-3, print_every=500, lbfgs_steps=800):
    model = MagneticPINN(hidden_layers=hidden_layers, neurons=neurons, hard_boundary=True).to(DEVICE)
    source = MagnetizationSource()
    material = MaterialPermeability()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1.0e-6)
    bc = BoundaryCondition(num_points=500)
    engine = torch.quasirandom.SobolEngine(dimension=2, scramble=True)
    
    history = {"pde": [], "boundary": []}
    
    for epoch in range(1, epochs + 1):
        optimizer.zero_grad(set_to_none=True)
        xy_collocation = sample_collocation_points(num_collocation, device=DEVICE, engine=engine)
        
        loss_pde, _ = compute_pde_loss(model, xy_collocation, source, material)
        
        xy_boundary = bc.sample_points(device=DEVICE)
        loss_bc = bc.loss(model, xy_boundary)
        
        loss = loss_pde
        loss.backward()
        
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        scheduler.step()
        
        history["pde"].append(loss_pde.item())
        history["boundary"].append(loss_bc.item())
        
        if epoch == 1 or epoch % print_every == 0:
            lr = optimizer.param_groups[0]["lr"]
            print(f"Adam Epoch {epoch:04d} | PDE = {loss_pde.item():.6e} | BC = {loss_bc.item():.6e} | LR = {lr:.3e}")

    lbfgs_optimizer = optim.LBFGS(
        model.parameters(),
        lr=0.8,
        max_iter=20,
        max_eval=25,
        history_size=50,
        tolerance_grad=1e-11,
        tolerance_change=1e-13,
        line_search_fn="strong_wolfe"
    )

    xy_collocation_fixed = sample_collocation_points(num_collocation, device=DEVICE, engine=engine)
    xy_boundary_fixed = bc.sample_points(device=DEVICE)

    step_count = [0]

    def closure():
        lbfgs_optimizer.zero_grad()
        loss_pde_val, _ = compute_pde_loss(model, xy_collocation_fixed, source, material)
        loss_bc_val = bc.loss(model, xy_boundary_fixed)
        total_loss = loss_pde_val
        total_loss.backward()
        step_count[0] += 1
        history["pde"].append(loss_pde_val.item())
        history["boundary"].append(loss_bc_val.item())
        if step_count[0] % 50 == 0:
            print(f"L-BFGS Step {step_count[0]:04d} | PDE = {loss_pde_val.item():.6e} | BC = {loss_bc_val.item():.6e}")
        return total_loss

    for _ in range(lbfgs_steps // 20):
        lbfgs_optimizer.step(closure)
            
    return model, history

def report_diagnostics(model, source, material):
    bc = BoundaryCondition(num_points=1000)
    boundary_points = bc.sample_points(device=DEVICE)
    max_boundary_error = bc.max_error(model, boundary_points)
    
    collocation = sample_collocation_points(12000, device=DEVICE)
    loss_pde, residual = compute_pde_loss(model, collocation, source, material)
    residual_rms = torch.sqrt(torch.mean(residual**2)).item()
    
    print("\n========================================")
    print("           PINN DIAGNOSTICS")
    print("========================================")
    print(f"Device                  : {DEVICE}")
    print(f"mu0                     : {MU0:.8e} H/m")
    print(f"MUR_IRON                : {MUR_IRON:.1f}")
    print(f"M0                      : {M0:.6e} A/m")
    print(f"L0                      : {L0:.6e} m")
    print(f"Boundary max |Az|       : {max_boundary_error:.8e} Wb/m")
    print(f"PDE MSE                 : {loss_pde.item():.8e}")
    print(f"PDE RMS residual        : {residual_rms:.8e}")
    print("========================================\n")

def plot_results(model, history):
    fields = evaluate_fields(model, resolution=160, device=DEVICE)
    X, Y = fields["X"], fields["Y"]
    Az, Bmag, Mx, dMx_dy = fields["Az"], fields["Bmag"], fields["Mx"], fields["dMx_dy"]
    Bx, By, Mur = fields["Bx"], fields["By"], fields["Mur"]
    
    fig, axes = plt.subplots(3, 3, figsize=(22, 18))
    
    contour00 = axes[0, 0].contourf(X, Y, Az, levels=60, cmap="jet")
    fig.colorbar(contour00, ax=axes[0, 0], label="A_z (Wb/m)")
    axes[0, 0].set_title("Magnetic Vector Potential $A_z$")
    
    contour01 = axes[0, 1].contourf(X, Y, Bmag, levels=60, cmap="jet")
    fig.colorbar(contour01, ax=axes[0, 1], label="|B| (T)")
    axes[0, 1].set_title("Magnetic Flux Density $|B|$")
    
    contour02 = axes[0, 2].contourf(X, Y, Mx, levels=60, cmap="viridis")
    fig.colorbar(contour02, ax=axes[0, 2], label="$M_x$ (A/m)")
    axes[0, 2].set_title("Prescribed Magnetization $M_x$")
    
    step = 7
    Bx_sub = Bx[::step, ::step]
    By_sub = By[::step, ::step]
    Bmag_sub = np.sqrt(Bx_sub**2 + By_sub**2)
    Bmag_clipped = np.clip(Bmag_sub, 0.0, 1.0)
    scale_factor = np.where(Bmag_sub > 1e-12, Bmag_clipped / (Bmag_sub + 1e-12), 0.0)
    Bx_limited = Bx_sub * scale_factor
    By_limited = By_sub * scale_factor
    axes[1, 0].contourf(X, Y, Bmag, levels=40, cmap="jet", alpha=0.25)
    axes[1, 0].quiver(X[::step, ::step], Y[::step, ::step], Bx_limited, By_limited, scale=4.0, pivot="mid")
    axes[1, 0].set_title("Magnetic Flux Density Vector $\\mathbf{B}$")
    
    contour11 = axes[1, 1].contourf(X, Y, dMx_dy, levels=60, cmap="coolwarm")
    fig.colorbar(contour11, ax=axes[1, 1], label=r"$\partial M_x/\partial y$ (A/m$^2$)")
    axes[1, 1].set_title("Magnetization Source Term")
    
    contour12 = axes[1, 2].contourf(X, Y, Mur, levels=60, cmap="copper")
    fig.colorbar(contour12, ax=axes[1, 2], label=r"$\mu_r$")
    axes[1, 2].set_title("Relative Permeability $\\mu_r$ (Iron Yoke Profile)")
    
    material_map = np.zeros_like(X)
    mag_mask = np.abs(Mx) > (0.1 * M0)
    iron_mask = Mur > 10.0
    material_map[mag_mask] = 1.0
    material_map[iron_mask] = 2.0
    contour20 = axes[2, 0].contourf(X, Y, material_map, levels=[-0.5, 0.5, 1.5, 2.5], cmap="tab10")
    cbar20 = fig.colorbar(contour20, ax=axes[2, 0], ticks=[0, 1, 2])
    cbar20.ax.set_yticklabels(["Air", "Magnets", "Iron Yoke"])
    axes[2, 0].set_title("Geometric Domains / Material Map")
    
    dx = X[0, 1] - X[0, 0]
    rho_m = -np.gradient(Mx, dx, axis=1)
    contour21 = axes[2, 1].contourf(X, Y, rho_m, levels=60, cmap="bwr")
    fig.colorbar(contour21, ax=axes[2, 1], label=r"$-\partial M_x/\partial x$ (Poles)")
    axes[2, 1].set_title("Magnetic Charge Density $\\rho_m$ (Poles N/S)")
    
    axes[2, 2].semilogy(history["pde"], label="PDE loss")
    axes[2, 2].semilogy(history["boundary"], label="Boundary error")
    axes[2, 2].set_title("Training History")
    axes[2, 2].legend()
    axes[2, 2].grid(True, alpha=0.3)
    
    for ax in [axes[0, 0], axes[0, 1], axes[0, 2], axes[1, 0], axes[1, 1], axes[1, 2], axes[2, 0], axes[2, 1]]:
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel("x (m)")
        ax.set_ylabel("y (m)")
        
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    trained_model, history = train_pinn(epochs=6000, num_collocation=12000, hidden_layers=6, neurons=128, learning_rate=1.0e-3, lbfgs_steps=800)
    source = MagnetizationSource()
    material = MaterialPermeability()
    report_diagnostics(trained_model, source, material)
    plot_results(trained_model, history)