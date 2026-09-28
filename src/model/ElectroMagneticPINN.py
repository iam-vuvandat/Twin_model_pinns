import torch
import torch.nn as nn
from typing import Callable, Optional, Dict, Tuple


class ElectroMagneticPINN(nn.Module):
    """
    2D Magnetostatic Physics-Informed Neural Network (PINN)

    The network learns the magnetic vector potential:

        A_z = f_theta(x, y)

    From A_z:

        B_x = dA_z/dy
        B_y = -dA_z/dx

    The magnetic field H can be obtained from:

        H = B / mu

    for linear/nonlinear materials.

    Physics equation:

        curl(H)_z - J_z = 0

    i.e.

        dH_y/dx - dH_x/dy - J_z = 0

    The final loss is:

        L =
            lambda_physics * L_physics
          + lambda_bc      * L_bc
          + lambda_data    * L_data
    """

    def __init__(
        self,
        input_dim: int = 2,
        hidden_layers: int = 4,
        neurons: int = 64,
        output_dim: int = 1,
        activation: str = "tanh",
        mu0: float = 4.0e-7 * torch.pi,
        mu_fn: Optional[Callable[[torch.Tensor], torch.Tensor]] = None,
        h_of_b_fn: Optional[Callable[[torch.Tensor], torch.Tensor]] = None,
        device: Optional[torch.device] = None,
        dtype: torch.dtype = torch.float32,
    ):
        super().__init__()

        if input_dim != 2:
            raise ValueError("This implementation is for 2D input (x, y).")

        if output_dim != 1:
            raise ValueError("This implementation expects one output: A_z.")

        if hidden_layers < 1:
            raise ValueError("hidden_layers must be >= 1.")

        if neurons < 1:
            raise ValueError("neurons must be >= 1.")

        if mu_fn is not None and h_of_b_fn is not None:
            raise ValueError(
                "Use either mu_fn or h_of_b_fn, not both."
            )

        self.mu0 = mu0
        self.mu_fn = mu_fn
        self.h_of_b_fn = h_of_b_fn
        self.device_ = device
        self.dtype_ = dtype

        # ---------------------------------------------------------
        # Activation
        # ---------------------------------------------------------
        if activation.lower() == "tanh":
            activation_layer = nn.Tanh
        elif activation.lower() == "silu":
            activation_layer = nn.SiLU
        elif activation.lower() == "gelu":
            activation_layer = nn.GELU
        elif activation.lower() == "relu":
            activation_layer = nn.ReLU
        else:
            raise ValueError(
                f"Unsupported activation: {activation}"
            )

        # ---------------------------------------------------------
        # Neural network
        # ---------------------------------------------------------
        layers = []

        layers.append(nn.Linear(input_dim, neurons))
        layers.append(activation_layer())

        for _ in range(hidden_layers - 1):
            layers.append(nn.Linear(neurons, neurons))
            layers.append(activation_layer())

        layers.append(nn.Linear(neurons, output_dim))

        self.network = nn.Sequential(*layers)

        # ---------------------------------------------------------
        # Xavier initialization
        # ---------------------------------------------------------
        self._initialize_weights()

        if device is not None:
            self.to(device=device, dtype=dtype)
        else:
            self.to(dtype=dtype)

    # =============================================================
    # Initialization
    # =============================================================

    def _initialize_weights(self) -> None:
        """
        Xavier initialization for linear layers.
        """

        for module in self.network:

            if isinstance(module, nn.Linear):
                nn.init.xavier_normal_(module.weight)

                if module.bias is not None:
                    nn.init.zeros_(module.bias)

    # =============================================================
    # Forward
    # =============================================================

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Parameters
        ----------
        x : torch.Tensor
            Shape: [N, 2]
            Columns:
                x[:, 0] = x coordinate
                x[:, 1] = y coordinate

        Returns
        -------
        A_z : torch.Tensor
            Shape: [N, 1]
        """

        if x.ndim != 2 or x.shape[1] != 2:
            raise ValueError(
                "Input x must have shape [N, 2]."
            )

        return self.network(x)

    # =============================================================
    # Autograd helper
    # =============================================================

    @staticmethod
    def _gradient(
        y: torch.Tensor,
        x: torch.Tensor,
    ) -> torch.Tensor:
        """
        Computes dy/dx using PyTorch autograd.

        y : [N, 1]
        x : [N, 2]

        return : [N, 2]
        """

        return torch.autograd.grad(
            outputs=y,
            inputs=x,
            grad_outputs=torch.ones_like(y),
            create_graph=True,
            retain_graph=True,
            only_inputs=True,
        )[0]

    # =============================================================
    # Magnetic vector potential derivatives
    # =============================================================

    def potential_and_derivatives(
        self,
        x: torch.Tensor,
    ) -> Dict[str, torch.Tensor]:
        """
        Calculate A_z and its first/second derivatives.

        Returns
        -------
        dict containing:

            A
            Ax
            Ay
            Axx
            Axy
            Ayx
            Ayy
        """

        x = x.clone().detach().requires_grad_(True)

        A = self.forward(x)

        # First derivatives
        grad_A = self._gradient(A, x)

        Ax = grad_A[:, 0:1]
        Ay = grad_A[:, 1:2]

        # Second derivatives
        grad_Ax = self._gradient(Ax, x)
        grad_Ay = self._gradient(Ay, x)

        Axx = grad_Ax[:, 0:1]
        Axy = grad_Ax[:, 1:2]

        Ayx = grad_Ay[:, 0:1]
        Ayy = grad_Ay[:, 1:2]

        return {
            "x": x,
            "A": A,
            "Ax": Ax,
            "Ay": Ay,
            "Axx": Axx,
            "Axy": Axy,
            "Ayx": Ayx,
            "Ayy": Ayy,
        }

    # =============================================================
    # Magnetic flux density
    # =============================================================

    def magnetic_flux_density(
        self,
        x: torch.Tensor,
    ) -> Dict[str, torch.Tensor]:
        """
        Compute B from magnetic vector potential A_z.

            B_x = dA_z/dy
            B_y = -dA_z/dx
        """

        result = self.potential_and_derivatives(x)

        A = result["A"]
        Ax = result["Ax"]
        Ay = result["Ay"]

        Bx = Ay
        By = -Ax

        Bmag = torch.sqrt(
            Bx * Bx +
            By * By +
            1.0e-12
        )

        return {
            **result,
            "Bx": Bx,
            "By": By,
            "Bmag": Bmag,
        }

    # =============================================================
    # Constitutive relation
    # =============================================================

    def magnetic_field(
        self,
        Bx: torch.Tensor,
        By: torch.Tensor,
        Bmag: torch.Tensor,
    ) -> Dict[str, torch.Tensor]:
        """
        Convert B -> H.

        Three possible cases:

        1. Constant permeability:
               H = B / mu0

        2. User-provided mu_fn(Bmag):
               H = B / mu(B)

        3. User-provided h_of_b_fn(Bmag):
               Hmag = H(B)
               H = Hmag * B / |B|

        The third form is convenient for a nonlinear B-H curve.
        """

        # ---------------------------------------------------------
        # Nonlinear B-H relation specified directly
        # ---------------------------------------------------------
        if self.h_of_b_fn is not None:

            Hmag = self.h_of_b_fn(Bmag)

            factor = Hmag / torch.clamp(
                Bmag,
                min=1.0e-12
            )

            Hx = factor * Bx
            Hy = factor * By

            mu_eff = torch.clamp(
                Bmag / torch.clamp(Hmag, min=1.0e-12),
                min=1.0e-12
            )

        # ---------------------------------------------------------
        # Permeability function mu(B)
        # ---------------------------------------------------------
        elif self.mu_fn is not None:

            mu = self.mu_fn(Bmag)

            mu = torch.clamp(
                mu,
                min=1.0e-12
            )

            Hx = Bx / mu
            Hy = By / mu

            mu_eff = mu

        # ---------------------------------------------------------
        # Constant permeability
        # ---------------------------------------------------------
        else:

            Hx = Bx / self.mu0
            Hy = By / self.mu0

            mu_eff = torch.full_like(
                Bmag,
                self.mu0
            )

        Hmag = torch.sqrt(
            Hx * Hx +
            Hy * Hy +
            1.0e-12
        )

        return {
            "Hx": Hx,
            "Hy": Hy,
            "Hmag": Hmag,
            "mu_eff": mu_eff,
        }

    # =============================================================
    # Complete electromagnetic state
    # =============================================================

    def electromagnetic_state(
        self,
        x: torch.Tensor,
    ) -> Dict[str, torch.Tensor]:
        """
        Compute A, B and H.
        """

        result = self.magnetic_flux_density(x)

        Bx = result["Bx"]
        By = result["By"]
        Bmag = result["Bmag"]

        H = self.magnetic_field(
            Bx,
            By,
            Bmag
        )

        return {
            **result,
            **H,
        }

    # =============================================================
    # Source current density
    # =============================================================

    @staticmethod
    def _evaluate_source(
        x: torch.Tensor,
        Jz: Optional[
            torch.Tensor |
            float |
            Callable[[torch.Tensor], torch.Tensor]
        ],
    ) -> torch.Tensor:

        if Jz is None:
            return torch.zeros(
                (x.shape[0], 1),
                dtype=x.dtype,
                device=x.device,
            )

        if callable(Jz):
            J = Jz(x)

        elif torch.is_tensor(Jz):
            J = Jz.to(
                device=x.device,
                dtype=x.dtype
            )

        else:
            J = torch.full(
                (x.shape[0], 1),
                float(Jz),
                dtype=x.dtype,
                device=x.device,
            )

        if J.ndim == 1:
            J = J.unsqueeze(1)

        if J.shape != (x.shape[0], 1):
            raise ValueError(
                "Jz must have shape [N, 1]."
            )

        return J

    # =============================================================
    # Physics residual
    # =============================================================

    def physics_residual(
        self,
        x: torch.Tensor,
        Jz: Optional[
            torch.Tensor |
            float |
            Callable[[torch.Tensor], torch.Tensor]
        ] = None,
    ) -> torch.Tensor:
        """
        Maxwell/Ampere residual.

            dH_y/dx - dH_x/dy - J_z = 0

        Returns
        -------
        residual : [N, 1]
        """

        x = x.clone().detach().requires_grad_(True)

        state = self.electromagnetic_state(x)

        Hx = state["Hx"]
        Hy = state["Hy"]

        dHx = self._gradient(Hx, x)
        dHy = self._gradient(Hy, x)

        dHx_dy = dHx[:, 1:2]
        dHy_dx = dHy[:, 0:1]

        J = self._evaluate_source(x, Jz)

        residual = dHy_dx - dHx_dy - J

        return residual

    # =============================================================
    # Physics loss
    # =============================================================

    def physics_loss(
        self,
        x: torch.Tensor,
        Jz: Optional[
            torch.Tensor |
            float |
            Callable[[torch.Tensor], torch.Tensor]
        ] = None,
    ) -> torch.Tensor:
        """
        Scalar physics loss:

            L_physics = mean(residual^2)
        """

        residual = self.physics_residual(
            x,
            Jz
        )

        return torch.mean(
            residual ** 2
        )

    # =============================================================
    # Boundary loss
    # =============================================================

    def boundary_loss(
        self,
        x_boundary: torch.Tensor,
        A_boundary: torch.Tensor |
        float |
        Callable[[torch.Tensor], torch.Tensor],
    ) -> torch.Tensor:
        """
        Dirichlet boundary condition:

            A_z(x_boundary) = A_boundary
        """

        x_boundary = x_boundary.to(
            device=next(self.parameters()).device,
            dtype=next(self.parameters()).dtype,
        )

        predicted = self.forward(x_boundary)

        if callable(A_boundary):
            target = A_boundary(x_boundary)

        elif torch.is_tensor(A_boundary):
            target = A_boundary.to(
                device=predicted.device,
                dtype=predicted.dtype,
            )

        else:
            target = torch.full_like(
                predicted,
                float(A_boundary)
            )

        if target.ndim == 1:
            target = target.unsqueeze(1)

        return torch.mean(
            (predicted - target) ** 2
        )

    # =============================================================
    # Data loss
    # =============================================================

    def data_loss(
        self,
        x_data: torch.Tensor,
        A_data: torch.Tensor,
    ) -> torch.Tensor:
        """
        Optional supervised loss against known A_z data.

            L_data = MSE(A_pred, A_data)
        """

        x_data = x_data.to(
            device=next(self.parameters()).device,
            dtype=next(self.parameters()).dtype,
        )

        A_data = A_data.to(
            device=x_data.device,
            dtype=x_data.dtype,
        )

        if A_data.ndim == 1:
            A_data = A_data.unsqueeze(1)

        predicted = self.forward(x_data)

        return torch.mean(
            (predicted - A_data) ** 2
        )

    # =============================================================
    # Total loss
    # =============================================================

    def total_loss(
        self,
        x_collocation: torch.Tensor,
        Jz=None,
        x_boundary: Optional[torch.Tensor] = None,
        A_boundary=None,
        x_data: Optional[torch.Tensor] = None,
        A_data: Optional[torch.Tensor] = None,
        lambda_physics: float = 1.0,
        lambda_bc: float = 1.0,
        lambda_data: float = 1.0,
    ) -> Tuple[
        torch.Tensor,
        Dict[str, torch.Tensor]
    ]:
        """
        Complete scalar PINN loss.
        """

        L_physics = self.physics_loss(
            x_collocation,
            Jz
        )

        L_bc = torch.zeros(
            (),
            dtype=L_physics.dtype,
            device=L_physics.device,
        )

        L_data = torch.zeros_like(
            L_physics
        )

        # ---------------------------------------------------------
        # Boundary condition
        # ---------------------------------------------------------
        if (
            x_boundary is not None
            and A_boundary is not None
        ):
            L_bc = self.boundary_loss(
                x_boundary,
                A_boundary
            )

        # ---------------------------------------------------------
        # Optional FEM/experimental data
        # ---------------------------------------------------------
        if (
            x_data is not None
            and A_data is not None
        ):
            L_data = self.data_loss(
                x_data,
                A_data
            )

        # ---------------------------------------------------------
        # Total scalar loss
        # ---------------------------------------------------------
        L_total = (
            lambda_physics * L_physics
            + lambda_bc * L_bc
            + lambda_data * L_data
        )

        losses = {
            "total": L_total,
            "physics": L_physics,
            "boundary": L_bc,
            "data": L_data,
        }

        return L_total, losses

    # =============================================================
    # Training
    # =============================================================

    def fit(
        self,
        x_collocation: torch.Tensor,
        Jz=None,
        x_boundary: Optional[torch.Tensor] = None,
        A_boundary=None,
        x_data: Optional[torch.Tensor] = None,
        A_data: Optional[torch.Tensor] = None,
        epochs: int = 5000,
        learning_rate: float = 1.0e-3,
        lambda_physics: float = 1.0,
        lambda_bc: float = 10.0,
        lambda_data: float = 1.0,
        optimizer_name: str = "adam",
        print_every: int = 500,
        use_lbfgs: bool = False,
        lbfgs_max_iter: int = 500,
    ):
        """
        Train the PINN.

        Returns
        -------
        history : dict
            Lists containing total, physics, boundary and data loss.
        """

        device = next(self.parameters()).device
        dtype = next(self.parameters()).dtype

        x_collocation = x_collocation.to(
            device=device,
            dtype=dtype
        )

        if x_boundary is not None:
            x_boundary = x_boundary.to(
                device=device,
                dtype=dtype
            )

        if A_boundary is not None and torch.is_tensor(A_boundary):
            A_boundary = A_boundary.to(
                device=device,
                dtype=dtype
            )

        if x_data is not None:
            x_data = x_data.to(
                device=device,
                dtype=dtype
            )

        if A_data is not None:
            A_data = A_data.to(
                device=device,
                dtype=dtype
            )

        # ---------------------------------------------------------
        # Optimizer
        # ---------------------------------------------------------
        if optimizer_name.lower() == "adam":

            optimizer = torch.optim.Adam(
                self.parameters(),
                lr=learning_rate
            )

        elif optimizer_name.lower() == "adamw":

            optimizer = torch.optim.AdamW(
                self.parameters(),
                lr=learning_rate
            )

        elif optimizer_name.lower() == "lbfgs":

            optimizer = torch.optim.LBFGS(
                self.parameters(),
                lr=learning_rate,
                max_iter=lbfgs_max_iter,
                max_eval=lbfgs_max_iter,
                tolerance_grad=1.0e-9,
                tolerance_change=1.0e-12,
                history_size=100,
                line_search_fn="strong_wolfe",
            )

        else:
            raise ValueError(
                "optimizer_name must be 'adam', "
                "'adamw' or 'lbfgs'."
            )

        history = {
            "total": [],
            "physics": [],
            "boundary": [],
            "data": [],
        }

        # =========================================================
        # Adam / AdamW training
        # =========================================================

        if optimizer_name.lower() in ("adam", "adamw"):

            for epoch in range(1, epochs + 1):

                optimizer.zero_grad(
                    set_to_none=True
                )

                total, losses = self.total_loss(
                    x_collocation=x_collocation,
                    Jz=Jz,
                    x_boundary=x_boundary,
                    A_boundary=A_boundary,
                    x_data=x_data,
                    A_data=A_data,
                    lambda_physics=lambda_physics,
                    lambda_bc=lambda_bc,
                    lambda_data=lambda_data,
                )

                total.backward()

                optimizer.step()

                # Save history
                history["total"].append(
                    total.detach().item()
                )

                history["physics"].append(
                    losses["physics"].detach().item()
                )

                history["boundary"].append(
                    losses["boundary"].detach().item()
                )

                history["data"].append(
                    losses["data"].detach().item()
                )

                if (
                    print_every > 0
                    and (
                        epoch == 1
                        or epoch % print_every == 0
                        or epoch == epochs
                    )
                ):
                    print(
                        f"Epoch {epoch:6d} | "
                        f"Total = {total.item():.6e} | "
                        f"Physics = {losses['physics'].item():.6e} | "
                        f"BC = {losses['boundary'].item():.6e} | "
                        f"Data = {losses['data'].item():.6e}"
                    )

        # =========================================================
        # Optional LBFGS refinement
        # =========================================================

        if use_lbfgs:

            lbfgs = torch.optim.LBFGS(
                self.parameters(),
                lr=1.0,
                max_iter=lbfgs_max_iter,
                max_eval=lbfgs_max_iter * 2,
                tolerance_grad=1.0e-9,
                tolerance_change=1.0e-12,
                history_size=100,
                line_search_fn="strong_wolfe",
            )

            def closure():

                lbfgs.zero_grad(
                    set_to_none=True
                )

                total, _ = self.total_loss(
                    x_collocation=x_collocation,
                    Jz=Jz,
                    x_boundary=x_boundary,
                    A_boundary=A_boundary,
                    x_data=x_data,
                    A_data=A_data,
                    lambda_physics=lambda_physics,
                    lambda_bc=lambda_bc,
                    lambda_data=lambda_data,
                )

                total.backward()

                return total

            lbfgs.step(closure)

        return history

    # =============================================================
    # Prediction
    # =============================================================

    @torch.no_grad()
    def predict_A(
        self,
        x: torch.Tensor,
    ) -> torch.Tensor:
        """
        Predict A_z without calculating derivatives.
        """

        device = next(self.parameters()).device
        dtype = next(self.parameters()).dtype

        x = x.to(
            device=device,
            dtype=dtype
        )

        return self.forward(x)

    def predict_B(
        self,
        x: torch.Tensor,
    ) -> Dict[str, torch.Tensor]:
        """
        Predict B_x, B_y and |B|.
        """

        device = next(self.parameters()).device
        dtype = next(self.parameters()).dtype

        x = x.to(
            device=device,
            dtype=dtype
        )

        self.eval()

        with torch.enable_grad():

            state = self.electromagnetic_state(x)

        return {
            "A": state["A"].detach(),
            "Bx": state["Bx"].detach(),
            "By": state["By"].detach(),
            "Bmag": state["Bmag"].detach(),
        }

    def predict_H(
        self,
        x: torch.Tensor,
    ) -> Dict[str, torch.Tensor]:
        """
        Predict H_x, H_y and |H|.
        """

        device = next(self.parameters()).device
        dtype = next(self.parameters()).dtype

        x = x.to(
            device=device,
            dtype=dtype
        )

        self.eval()

        with torch.enable_grad():

            state = self.electromagnetic_state(x)

        return {
            "A": state["A"].detach(),
            "Hx": state["Hx"].detach(),
            "Hy": state["Hy"].detach(),
            "Hmag": state["Hmag"].detach(),
            "mu_eff": state["mu_eff"].detach(),
        }