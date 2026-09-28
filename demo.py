import math
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import matplotlib.pyplot as plt


# ============================================================
# Global configuration
# ============================================================

SEED = 42

torch.manual_seed(SEED)
np.random.seed(SEED)

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

DTYPE = torch.float32

if torch.cuda.is_available():
    torch.set_float32_matmul_precision("high")
    print(
        f"[DEBUG] Device: GPU "
        f"({torch.cuda.get_device_name(0)})"
    )
else:
    print("[DEBUG] Device: CPU")


# ============================================================
# Physical constants / normalization
# ============================================================

MU0 = 4.0 * math.pi * 1.0e-7

MUR_IRON_LINEAR = 400.0
B_SAT_SCALE = 1.5  # Tesla (Knee point for magnetic saturation)

M0 = 1.0e6
L0 = 1.0

A0 = MU0 * M0 * L0
B0 = MU0 * M0


# ============================================================
# Geometry
# ============================================================

DOMAIN_EXTENT = 2.0

LENGTH_X = 0.30
WIDTH_Y = 0.12
STEEPNESS = 60.0

MAGNET_OFFSET_X = 1.1 * LENGTH_X
SPAN_X = MAGNET_OFFSET_X + LENGTH_X

YOKE_LENGTH_X = 1.10 * SPAN_X
YOKE_WIDTH_Y = WIDTH_Y
YOKE_OFFSET_Y = -(2.0 * WIDTH_Y)


# ============================================================
# Magnet polarity
# ============================================================

LEFT_POLARITY = -1.0
RIGHT_POLARITY = +1.0


# ============================================================
# Magnetization source
# ============================================================

class MagnetizationSource:

    def __init__(
        self,
        length_x=LENGTH_X,
        width_y=WIDTH_Y,
        offset_x=MAGNET_OFFSET_X,
        steepness=STEEPNESS,
        left_polarity=LEFT_POLARITY,
        right_polarity=RIGHT_POLARITY
    ):
        self.lx = float(length_x)
        self.wy = float(width_y)
        self.offset_x = float(offset_x)
        self.k = float(steepness)

        self.left_polarity = float(left_polarity)
        self.right_polarity = float(right_polarity)

    def dimensionless(self, xy):
        x = xy[:, 0:1]
        y = xy[:, 1:2]

        sig_x_left = (
            torch.sigmoid(self.k * (x + self.offset_x + self.lx))
            - torch.sigmoid(self.k * (x + self.offset_x - self.lx))
        )

        sig_x_right = (
            torch.sigmoid(self.k * (x - self.offset_x + self.lx))
            - torch.sigmoid(self.k * (x - self.offset_x - self.lx))
        )

        sig_y = (
            torch.sigmoid(self.k * (y + self.wy))
            - torch.sigmoid(self.k * (y - self.wy))
        )

        return (
            self.left_polarity * sig_x_left
            + self.right_polarity * sig_x_right
        ) * sig_y

    def physical(self, xy):
        return M0 * self.dimensionless(xy)

    def dmx_dy_dimensionless(self, xy):
        x = xy[:, 0:1]
        y = xy[:, 1:2]

        sig_x_left = (
            torch.sigmoid(self.k * (x + self.offset_x + self.lx))
            - torch.sigmoid(self.k * (x + self.offset_x - self.lx))
        )

        sig_x_right = (
            torch.sigmoid(self.k * (x - self.offset_x + self.lx))
            - torch.sigmoid(self.k * (x - self.offset_x - self.lx))
        )

        s_y_plus = torch.sigmoid(self.k * (y + self.wy))
        s_y_minus = torch.sigmoid(self.k * (y - self.wy))

        ds_y = (
            self.k * s_y_plus * (1.0 - s_y_plus)
            - self.k * s_y_minus * (1.0 - s_y_minus)
        )

        return (
            self.left_polarity * sig_x_left
            + self.right_polarity * sig_x_right
        ) * ds_y

    def dmx_dy_physical(self, xy):
        return (M0 / L0) * self.dmx_dy_dimensionless(xy)


# ============================================================
# Material model (Curriculum Learning Enabled)
# ============================================================

class MaterialPermeability:

    def __init__(
        self,
        yoke_lx=YOKE_LENGTH_X,
        yoke_wy=YOKE_WIDTH_Y,
        yoke_offset_y=YOKE_OFFSET_Y,
        mur_linear=MUR_IRON_LINEAR,
        b_scale=B_SAT_SCALE,
        steepness=STEEPNESS
    ):
        self.lx = float(yoke_lx)
        self.wy = float(yoke_wy)
        self.y0 = float(yoke_offset_y)

        self.mur_linear = float(mur_linear)
        self.b_scale = float(b_scale)
        self.k = float(steepness)
        self.nu_air = 1.0
        
        # Flag to toggle B-H curve
        self.use_nonlinear = False

    def iron_mask(self, xy):
        x = xy[:, 0:1]
        y = xy[:, 1:2]

        sig_x = (
            torch.sigmoid(self.k * (x + self.lx))
            - torch.sigmoid(self.k * (x - self.lx))
        )

        sig_y = (
            torch.sigmoid(self.k * (y - self.y0 + self.wy))
            - torch.sigmoid(self.k * (y - self.y0 - self.wy))
        )

        return sig_x * sig_y

    def nu_r_dimensionless(self, xy, dAz_dx=None, dAz_dy=None):
        mask_iron = self.iron_mask(xy)

        if self.use_nonlinear and dAz_dx is not None and dAz_dy is not None:
            # Non-linear B-H curve
            B_mag_sq = (B0**2) * (dAz_dx**2 + dAz_dy**2)
            mur_local = 1.0 + (self.mur_linear - 1.0) / (1.0 + B_mag_sq / (self.b_scale**2))
            nu_iron_local = 1.0 / mur_local
        else:
            # Linear assumption
            nu_iron_local = 1.0 / self.mur_linear

        return self.nu_air + (nu_iron_local - self.nu_air) * mask_iron

    def mu_r_dimensionless(self, xy, dAz_dx=None, dAz_dy=None):
        return 1.0 / self.nu_r_dimensionless(xy, dAz_dx, dAz_dy)


# ============================================================
# Boundary condition
# ============================================================

class BoundaryCondition:

    def __init__(
        self,
        x_min=-DOMAIN_EXTENT,
        x_max=DOMAIN_EXTENT,
        y_min=-DOMAIN_EXTENT,
        y_max=DOMAIN_EXTENT,
        num_points=1000
    ):
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

        return torch.cat([
            torch.cat([x_bottom, y_bottom], dim=1),
            torch.cat([x_top, y_top], dim=1),
            torch.cat([x_left, y_left], dim=1),
            torch.cat([x_right, y_right], dim=1)
        ], dim=0)

    @staticmethod
    def max_error(model, points):
        with torch.no_grad():
            Az = model(points)
        return torch.max(torch.abs(Az)).item()


# ============================================================
# PINN model
# ============================================================

class MagneticPINN(nn.Module):

    def __init__(
        self,
        hidden_layers=6,
        neurons=128,
        hard_boundary=True
    ):
        super().__init__()
        self.hard_boundary = hard_boundary

        layers = [nn.Linear(2, neurons), nn.Tanh()]
        for _ in range(hidden_layers - 1):
            layers += [nn.Linear(neurons, neurons), nn.Tanh()]
        layers.append(nn.Linear(neurons, 1))

        self.net = nn.Sequential(*layers)
        self._initialize_weights()

    def _initialize_weights(self):
        for module in self.net:
            if isinstance(module, nn.Linear):
                nn.init.xavier_normal_(module.weight)
                nn.init.zeros_(module.bias)

    def boundary_factor(self, xy):
        x = xy[:, 0:1]
        y = xy[:, 1:2]
        return (1.0 - (x / DOMAIN_EXTENT)**2) * (1.0 - (y / DOMAIN_EXTENT)**2)

    def forward(self, xy):
        raw = self.net(xy)
        if self.hard_boundary:
            return self.boundary_factor(xy) * raw
        return raw


# ============================================================
# Sobol sampling
# ============================================================

def create_sobol_engine(seed=SEED):
    return torch.quasirandom.SobolEngine(dimension=2, scramble=True, seed=seed)

def sample_collocation_points(
    num_points,
    x_min=-DOMAIN_EXTENT,
    x_max=DOMAIN_EXTENT,
    y_min=-DOMAIN_EXTENT,
    y_max=DOMAIN_EXTENT,
    device=DEVICE,
    engine=None
):
    if engine is None:
        engine = create_sobol_engine()

    uv = engine.draw(num_points).to(device=device, dtype=DTYPE)
    x = x_min + (x_max - x_min) * uv[:, 0:1]
    y = y_min + (y_max - y_min) * uv[:, 1:2]

    xy = torch.cat([x, y], dim=1)
    xy.requires_grad_(True)
    return xy


# ============================================================
# PDE residual
# ============================================================

def compute_pde_loss(model, xy_collocation, source, material):
    Az_star = model(xy_collocation)

    grads = torch.autograd.grad(
        outputs=Az_star, inputs=xy_collocation,
        grad_outputs=torch.ones_like(Az_star), create_graph=True
    )[0]

    dAz_dx = grads[:, 0:1]
    dAz_dy = grads[:, 1:2]

    nu_r = material.nu_r_dimensionless(xy_collocation, dAz_dx, dAz_dy)

    flux_x = nu_r * dAz_dx
    flux_y = nu_r * dAz_dy

    div_flux_x = torch.autograd.grad(
        outputs=flux_x, inputs=xy_collocation,
        grad_outputs=torch.ones_like(flux_x), create_graph=True, retain_graph=True
    )[0][:, 0:1]

    div_flux_y = torch.autograd.grad(
        outputs=flux_y, inputs=xy_collocation,
        grad_outputs=torch.ones_like(flux_y), create_graph=True
    )[0][:, 1:2]

    dMx_dy = source.dmx_dy_dimensionless(xy_collocation)
    residual = div_flux_x + div_flux_y - dMx_dy
    
    return torch.mean(residual**2), residual


# ============================================================
# Field evaluation
# ============================================================

def evaluate_fields(model, material, resolution=160, device=DEVICE):
    was_training = model.training
    model.eval()

    x_star = np.linspace(-DOMAIN_EXTENT, DOMAIN_EXTENT, resolution, dtype=np.float32)
    y_star = np.linspace(-DOMAIN_EXTENT, DOMAIN_EXTENT, resolution, dtype=np.float32)
    X_star, Y_star = np.meshgrid(x_star, y_star)

    xy_np = np.column_stack((X_star.ravel(), Y_star.ravel())).astype(np.float32)
    xy = torch.tensor(xy_np, device=device, dtype=DTYPE, requires_grad=True)

    Az_star = model(xy)
    grads = torch.autograd.grad(
        outputs=Az_star, inputs=xy,
        grad_outputs=torch.ones_like(Az_star), create_graph=False
    )[0]

    dAz_dx = grads[:, 0:1]
    dAz_dy = grads[:, 1:2]

    Az = (A0 * Az_star).detach().cpu().numpy().reshape(X_star.shape)
    Bx = (B0 * dAz_dy).detach().cpu().numpy().reshape(X_star.shape)
    By = (-B0 * dAz_dx).detach().cpu().numpy().reshape(X_star.shape)
    Bmag = np.sqrt(Bx**2 + By**2)

    source = MagnetizationSource()
    xy_detached = xy.detach()
    dAz_dx_detached = dAz_dx.detach()
    dAz_dy_detached = dAz_dy.detach()

    with torch.no_grad():
        Mx = source.physical(xy_detached).cpu().numpy().reshape(X_star.shape)
        dMx_dy = source.dmx_dy_physical(xy_detached).cpu().numpy().reshape(X_star.shape)
        Mur = material.mu_r_dimensionless(xy_detached, dAz_dx_detached, dAz_dy_detached).cpu().numpy().reshape(X_star.shape)

    X = L0 * X_star
    Y = L0 * Y_star

    if was_training:
        model.train()

    return {
        "X": X, "Y": Y, "Az": Az, "Bx": Bx, "By": By, "Bmag": Bmag, 
        "Mx": Mx, "dMx_dy": dMx_dy, "Mur": Mur
    }


# ============================================================
# Diagnostics
# ============================================================

def compute_boundary_flux(model, resolution=400, device=DEVICE):
    model.eval()
    t = torch.linspace(-DOMAIN_EXTENT, DOMAIN_EXTENT, resolution, device=device, dtype=DTYPE).reshape(-1, 1)

    bottom = torch.cat([t, torch.full_like(t, -DOMAIN_EXTENT)], dim=1)
    top = torch.cat([t, torch.full_like(t, DOMAIN_EXTENT)], dim=1)
    left = torch.cat([torch.full_like(t, -DOMAIN_EXTENT), t], dim=1)
    right = torch.cat([torch.full_like(t, DOMAIN_EXTENT), t], dim=1)

    def B_at(points):
        points = points.clone().requires_grad_(True)
        Az = model(points)
        grads = torch.autograd.grad(
            outputs=Az, inputs=points, grad_outputs=torch.ones_like(Az), create_graph=False
        )[0]
        bx = B0 * grads[:, 1:2]
        by = -B0 * grads[:, 0:1]
        return bx.detach().cpu().numpy().ravel(), by.detach().cpu().numpy().ravel()

    _, by_bottom = B_at(bottom)
    _, by_top = B_at(top)
    bx_left, _ = B_at(left)
    bx_right, _ = B_at(right)

    t_np = t.detach().cpu().numpy().ravel()
    phi_bottom = np.trapezoid(-by_bottom, t_np)
    phi_top = np.trapezoid(by_top, t_np)
    phi_left = np.trapezoid(-bx_left, t_np)
    phi_right = np.trapezoid(bx_right, t_np)

    return {
        "bottom": phi_bottom, "top": phi_top, "left": phi_left, 
        "right": phi_right, "total": phi_bottom + phi_top + phi_left + phi_right
    }

def report_diagnostics(model, source, material, num_validation=5000):
    model.eval()
    bc = BoundaryCondition(num_points=1000)
    boundary_points = bc.sample_points(device=DEVICE)
    max_boundary_error = bc.max_error(model, boundary_points)

    validation = sample_collocation_points(
        num_validation, device=DEVICE, engine=create_sobol_engine(seed=SEED + 100)
    )

    loss_pde, residual = compute_pde_loss(model, validation, source, material)
    residual_rms = torch.sqrt(torch.mean(residual**2)).item()

    fields = evaluate_fields(model, material, resolution=120, device=DEVICE)
    flux = compute_boundary_flux(model, resolution=300, device=DEVICE)

    print("\n========================================")
    print("             PINN DIAGNOSTICS")
    print("========================================")
    print(f"Device                 : {DEVICE}")
    print(f"Non-linear B-H Active  : {material.use_nonlinear}")
    print(f"B0                     : {B0:.6e} T")
    print(f"Iron mu_r (Linear)     : {MUR_IRON_LINEAR:.1f}")
    print("----------------------------------------")
    print(f"Boundary max |Az|      : {max_boundary_error:.8e} Wb/m")
    print(f"PDE MSE                : {loss_pde.item():.8e}")
    print(f"PDE RMS residual       : {residual_rms:.8e}")
    print(f"Bmax                   : {np.max(fields['Bmag']):.8e} T")
    print(f"Closed-boundary flux   : {flux['total']:.8e} Wb/m")
    print("========================================\n")


# ============================================================
# Transfer Learning (Curriculum Training)
# ============================================================

def train_pinn_curriculum(
    epochs_linear=3500,
    lbfgs_linear=200,
    epochs_nonlinear=1500,
    num_collocation=10000,
    hidden_layers=6,
    neurons=128
):
    model = MagneticPINN(hidden_layers=hidden_layers, neurons=neurons, hard_boundary=True).to(DEVICE)
    source = MagnetizationSource()
    material = MaterialPermeability()
    engine = create_sobol_engine(seed=SEED)

    history = {
        "adam_linear": [],
        "lbfgs_linear": [],
        "adam_nonlinear": []
    }

    # --------------------------------------------------------
    # PHASE 1: LINEAR MODEL (Fast convergence)
    # --------------------------------------------------------
    print("\n" + "="*50)
    print(" PHASE 1: LINEAR TRAINING (mu_r = const)")
    print("="*50)
    material.use_nonlinear = False
    
    adam1 = optim.Adam(model.parameters(), lr=1.0e-3)
    scheduler1 = optim.lr_scheduler.CosineAnnealingLR(adam1, T_max=epochs_linear, eta_min=1.0e-6)

    model.train()
    for epoch in range(1, epochs_linear + 1):
        adam1.zero_grad(set_to_none=True)
        xy_col = sample_collocation_points(num_collocation, device=DEVICE, engine=engine)
        loss_pde, _ = compute_pde_loss(model, xy_col, source, material)
        loss_pde.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        adam1.step()
        scheduler1.step()
        history["adam_linear"].append(loss_pde.item())

        if epoch == 1 or epoch % 500 == 0:
            print(f"[Phase 1 - Adam] Epoch {epoch:05d} | PDE Loss = {loss_pde.item():.6e}")

    print("\n[Phase 1 - L-BFGS] Fine-tuning linear solution...")
    lbfgs_engine = create_sobol_engine(seed=SEED + 1)
    xy_fixed = sample_collocation_points(5000, device=DEVICE, engine=lbfgs_engine)
    
    lbfgs = optim.LBFGS(model.parameters(), lr=0.8, max_iter=lbfgs_linear, line_search_fn="strong_wolfe")
    step_lbfgs = [0]
    
    def closure_linear():
        lbfgs.zero_grad(set_to_none=True)
        loss_pde, _ = compute_pde_loss(model, xy_fixed, source, material)
        loss_pde.backward()
        step_lbfgs[0] += 1
        history["lbfgs_linear"].append(loss_pde.item())
        if step_lbfgs[0] == 1 or step_lbfgs[0] % 50 == 0:
            print(f"L-BFGS Step {step_lbfgs[0]:04d} | PDE Loss = {loss_pde.item():.6e}")
        return loss_pde
    lbfgs.step(closure_linear)

    # --------------------------------------------------------
    # PHASE 2: NON-LINEAR FINE-TUNING (Transfer Learning)
    # --------------------------------------------------------
    print("\n" + "="*50)
    print(" PHASE 2: NON-LINEAR FINE-TUNING (B-H Curve Active)")
    print("="*50)
    material.use_nonlinear = True
    
    # Use a very small learning rate to avoid gradient explosion with the highly non-linear B-H curve
    adam2 = optim.Adam(model.parameters(), lr=5.0e-5)
    
    for epoch in range(1, epochs_nonlinear + 1):
        adam2.zero_grad(set_to_none=True)
        xy_col = sample_collocation_points(num_collocation, device=DEVICE, engine=engine)
        loss_pde, _ = compute_pde_loss(model, xy_col, source, material)
        loss_pde.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=0.5)
        adam2.step()
        history["adam_nonlinear"].append(loss_pde.item())

        if epoch == 1 or epoch % 250 == 0:
            print(f"[Phase 2 - Adam] Epoch {epoch:05d} | Non-linear PDE Loss = {loss_pde.item():.6e}")

    return model, history, material


# ============================================================
# Plot
# ============================================================

def plot_results(model, history, material, resolution=160):
    fields = evaluate_fields(model, material, resolution=resolution, device=DEVICE)

    X, Y = fields["X"], fields["Y"]
    Az, Bmag = fields["Az"], fields["Bmag"]
    Bx, By = fields["Bx"], fields["By"]
    Mx, dMx_dy = fields["Mx"], fields["dMx_dy"]
    Mur = fields["Mur"]

    fig, axes = plt.subplots(3, 4, figsize=(28, 18))

    # A_z
    contour = axes[0, 0].contourf(X, Y, Az, levels=60, cmap="jet")
    fig.colorbar(contour, ax=axes[0, 0], label="A_z (Wb/m)")
    axes[0, 0].set_title("Magnetic Vector Potential $A_z$")

    # |B|
    contour = axes[0, 1].contourf(X, Y, Bmag, levels=60, cmap="jet")
    fig.colorbar(contour, ax=axes[0, 1], label="|B| (T)")
    axes[0, 1].set_title("Magnetic Flux Density $|B|$")
    
    # B vector
    step = max(1, resolution // 25)
    X_sub, Y_sub = X[::step, ::step], Y[::step, ::step]
    Bx_sub, By_sub = Bx[::step, ::step], By[::step, ::step]
    Bsub = np.sqrt(Bx_sub**2 + By_sub**2)
    scale = np.maximum(Bsub, 1.0e-12)
    Bx_dir, By_dir = Bx_sub / scale, By_sub / scale

    axes[0, 2].contourf(X, Y, Bmag, levels=40, cmap="jet", alpha=0.25)
    axes[0, 2].quiver(X_sub, Y_sub, Bx_dir, By_dir, scale=25.0, pivot="mid")
    axes[0, 2].set_title("Magnetic Flux Density Vector $\\mathbf{B}$")

    # Analytical B-H Curve
    B_plot = np.linspace(0, 3.5, 300)
    mur_plot = 1.0 + (MUR_IRON_LINEAR - 1.0) / (1.0 + (B_plot / B_SAT_SCALE)**2)
    H_plot = B_plot / (MU0 * mur_plot)
    axes[0, 3].plot(H_plot, B_plot, 'b-', linewidth=3)
    axes[0, 3].set_xlabel("H (A/m)")
    axes[0, 3].set_ylabel("B (T)")
    axes[0, 3].set_title("B-H Curve (Iron Yoke Saturation)")
    axes[0, 3].grid(True, alpha=0.5)

    # Mx
    contour = axes[1, 0].contourf(X, Y, Mx, levels=60, cmap="viridis")
    fig.colorbar(contour, ax=axes[1, 0], label="$M_x$ (A/m)")
    axes[1, 0].set_title("Magnetization $M_x$")

    # dMx/dy
    contour = axes[1, 1].contourf(X, Y, dMx_dy, levels=60, cmap="coolwarm")
    fig.colorbar(contour, ax=axes[1, 1], label=r"$\partial M_x/\partial y$ (A/m$^2$)")
    axes[1, 1].set_title("Magnetization Source Term")

    # Material map
    material_map = np.zeros_like(X)
    mag_mask = np.abs(Mx) > 0.1 * M0
    xy_np = np.column_stack((X.ravel(), Y.ravel())).astype(np.float32)
    xy_tensor = torch.tensor(xy_np, device=DEVICE, dtype=DTYPE)
    iron_mask_tensor = material.iron_mask(xy_tensor).cpu().numpy().reshape(X.shape)
    iron_mask = iron_mask_tensor > 0.5

    material_map[iron_mask] = 2.0
    material_map[mag_mask & ~iron_mask] = 1.0

    contour = axes[1, 2].contourf(X, Y, material_map, levels=[-0.5, 0.5, 1.5, 2.5], cmap="tab10")
    cbar = fig.colorbar(contour, ax=axes[1, 2], ticks=[0, 1, 2])
    cbar.ax.set_yticklabels(["Air", "Magnets", "Iron Yoke"])
    axes[1, 2].set_title("Material Map")
    
    # Magnetic charge density
    rho_m = -np.gradient(Mx, X[0, 1] - X[0, 0], axis=1)
    contour = axes[1, 3].contourf(X, Y, rho_m, levels=60, cmap="bwr")
    fig.colorbar(contour, ax=axes[1, 3], label=r"$\rho_m=-\partial M_x/\partial x$ (A/m$^2$)")
    axes[1, 3].set_title("Magnetic Charge Density")

    # mu_r (Dynamic Permeability)
    contour = axes[2, 0].contourf(X, Y, Mur, levels=60, cmap="copper")
    fig.colorbar(contour, ax=axes[2, 0], label=r"$\mu_r(|B|)$")
    axes[2, 0].set_title("Dynamic Relative Permeability $\\mu_r$")

    # Training history (Curriculum split)
    adam_lin = np.asarray(history["adam_linear"])
    lbfgs_lin = np.asarray(history["lbfgs_linear"])
    adam_nonlin = np.asarray(history["adam_nonlinear"])

    total_len = 0
    if adam_lin.size > 0:
        axes[2, 1].semilogy(np.arange(1, len(adam_lin) + 1), np.maximum(adam_lin, 1e-20), label="Phase 1: Adam (Linear)")
        total_len += len(adam_lin)
    if lbfgs_lin.size > 0:
        axes[2, 1].semilogy(np.arange(total_len + 1, total_len + len(lbfgs_lin) + 1), np.maximum(lbfgs_lin, 1e-20), label="Phase 1: L-BFGS (Linear)")
        total_len += len(lbfgs_lin)
    if adam_nonlin.size > 0:
        axes[2, 1].semilogy(np.arange(total_len + 1, total_len + len(adam_nonlin) + 1), np.maximum(adam_nonlin, 1e-20), label="Phase 2: Adam (Non-linear Fine-tune)", color='red')

    axes[2, 1].set_title("PDE Curriculum Training History")
    axes[2, 1].set_xlabel("Training evaluation")
    axes[2, 1].set_ylabel("PDE loss")
    axes[2, 1].legend()
    axes[2, 1].grid(True, alpha=0.3)

    # Formatting
    axes[2, 2].axis('off')
    axes[2, 3].axis('off')

    plot_axes = [axes[0, 0], axes[0, 1], axes[0, 2], axes[1, 0], axes[1, 1], axes[1, 2], axes[1, 3], axes[2, 0]]
    for ax in plot_axes:
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel("x (m)")
        ax.set_ylabel("y (m)")

    plt.tight_layout()
    plt.show()


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    trained_model, history, final_material = train_pinn_curriculum(
        epochs_linear=3500,
        lbfgs_linear=200,
        epochs_nonlinear=1500,
        num_collocation=10000,
        hidden_layers=6,
        neurons=128
    )

    source = MagnetizationSource()
    report_diagnostics(trained_model, source, final_material, num_validation=5000)
    plot_results(trained_model, history, final_material, resolution=160)