"""
version 1.2.0 - Updated with Flexible PINN API and Steepness
"""
import os
import sys

current_directory = os.path.dirname(os.path.abspath(__file__))
if current_directory not in sys.path:
    sys.path.insert(0, current_directory)

import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt
from geometry_engine.geometry import Geometry
from geometry_engine.segment.segment import Segment
from physics_domain.collocation_sampler import CollocationSampler
from electro_magnetic_pinn import ElectroMagneticPINN

def main():
    geometry_instance = Geometry(steepness=5000.0)
    
    top_magnet_vertices = [
        [-0.03, 0.015],
        [0.03, 0.015],
        [0.03, 0.025],
        [-0.03, 0.025]
    ]
    top_magnet = Segment(top_magnet_vertices).set_material_properties(
        name="top_magnet",
        relative_permeability=1.05,
        coercive_field_x=800000.0,
        coercive_field_y=0.0
    )
    geometry_instance.add_segment(top_magnet)

    bottom_magnet_vertices = [
        [-0.03, -0.025],
        [0.03, -0.025],
        [0.03, -0.015],
        [-0.03, -0.015]
    ]
    bottom_magnet = Segment(bottom_magnet_vertices).set_material_properties(
        name="bottom_magnet",
        relative_permeability=1.05,
        coercive_field_x=-800000.0,
        coercive_field_y=0.0
    )
    geometry_instance.add_segment(bottom_magnet)
    
    collocation_sampler_instance = CollocationSampler(
        x_boundaries_tuple=(-0.05, 0.05),
        y_boundaries_tuple=(-0.05, 0.05)
    )

    geometry_instance.plot_problem_definition(
        x_boundaries_tuple=(-0.05, 0.05),
        y_boundaries_tuple=(-0.05, 0.05),
        resolution=100
    )

    # 2. Sử dụng API linh hoạt để cấu hình mạng PINN
    model = ElectroMagneticPINN(
        geometry_engine_instance=geometry_instance,
        collocation_sampler_instance=collocation_sampler_instance,
        hidden_layers=6,               # Thay đổi từ 4 lên 6 lớp
        hidden_neurons=64,             # Thay đổi từ 50 lên 64 nơ-ron
        activation_function=nn.Tanh()  # Đổi hàm kích hoạt sang Tanh
    )
    
    model.execute_training_process(
        number_of_uniform_points=2500,
        number_of_interface_points=800,
        distance_threshold=0.005,
        epochs_adam=800,
        epochs_lbfgs=100
    )
    
    print("Đang tạo biểu đồ trực quan hóa kết quả trường điện từ...")
    resolution = 120
    x_coords = np.linspace(-0.05, 0.05, resolution)
    y_coords = np.linspace(-0.05, 0.05, resolution)
    X_grid, Y_grid = np.meshgrid(x_coords, y_coords)
    
    xy_points_tensor = torch.tensor(np.column_stack((X_grid.ravel(), Y_grid.ravel())), dtype=torch.float32)
    
    A_z_pred, B_x_pred, B_y_pred = model.evaluate_fields(xy_points_tensor)
    
    A_z_grid = A_z_pred.numpy().reshape(resolution, resolution)
    B_x_grid = B_x_pred.numpy().reshape(resolution, resolution)
    B_y_grid = B_y_pred.numpy().reshape(resolution, resolution)
    B_mag_grid = np.sqrt(B_x_grid**2 + B_y_grid**2)
    
    # --- Figure 1: Các biểu đồ cường độ và thành phần (Contours) ---
    fig1, axs = plt.subplots(2, 2, figsize=(12, 10))
    
    contour_az = axs[0, 0].contourf(X_grid, Y_grid, A_z_grid, levels=60, cmap="jet")
    fig1.colorbar(contour_az, ax=axs[0, 0], label="A_z (Wb/m)")
    axs[0, 0].set_title("Magnetic Vector Potential ($A_z$)")
    axs[0, 0].set_xlabel("x (m)")
    axs[0, 0].set_ylabel("y (m)")
    axs[0, 0].set_aspect('equal')
    
    contour_b = axs[0, 1].contourf(X_grid, Y_grid, B_mag_grid, levels=60, cmap="rainbow")
    fig1.colorbar(contour_b, ax=axs[0, 1], label="|B| (T)")
    axs[0, 1].set_title("Magnetic Flux Density Magnitude ($|B|$)")
    axs[0, 1].set_xlabel("x (m)")
    axs[0, 1].set_ylabel("y (m)")
    axs[0, 1].set_aspect('equal')
    
    contour_bx = axs[1, 0].contourf(X_grid, Y_grid, B_x_grid, levels=60, cmap="coolwarm")
    fig1.colorbar(contour_bx, ax=axs[1, 0], label="B_x (T)")
    axs[1, 0].set_title("Magnetic Field Component ($B_x$)")
    axs[1, 0].set_xlabel("x (m)")
    axs[1, 0].set_ylabel("y (m)")
    axs[1, 0].set_aspect('equal')
    
    contour_by = axs[1, 1].contourf(X_grid, Y_grid, B_y_grid, levels=60, cmap="coolwarm")
    fig1.colorbar(contour_by, ax=axs[1, 1], label="B_y (T)")
    axs[1, 1].set_title("Magnetic Field Component ($B_y$)")
    axs[1, 1].set_xlabel("x (m)")
    axs[1, 1].set_ylabel("y (m)")
    axs[1, 1].set_aspect('equal')
    
    fig1.tight_layout()
    
    # --- Figure 2: Biểu đồ Vector Mật độ từ thông (Quiver plot) ---
    fig2, ax2 = plt.subplots(figsize=(8, 7))
    
    # Vẽ nền làm mờ hiển thị cường độ |B|
    contour_b_bg = ax2.contourf(X_grid, Y_grid, B_mag_grid, levels=60, cmap="rainbow", alpha=0.4)
    fig2.colorbar(contour_b_bg, ax=ax2, label="|B| (T)")
    
    # Lấy mẫu thưa hơn (stride = 4) để vẽ vector tránh bị rối do lưới 120x120 quá dày
    step = 4
    X_sub = X_grid[::step, ::step]
    Y_sub = Y_grid[::step, ::step]
    Bx_sub = B_x_grid[::step, ::step]
    By_sub = B_y_grid[::step, ::step]
    
    # Vẽ đồ thị vector (Quiver plot)
    ax2.quiver(X_sub, Y_sub, Bx_sub, By_sub, color='black', pivot='mid')
    
    ax2.set_title("Magnetic Flux Density Vectors (B)")
    ax2.set_xlabel("x (m)")
    ax2.set_ylabel("y (m)")
    ax2.set_aspect('equal')
    
    fig2.tight_layout()
    
    # Hiển thị tất cả các biểu đồ
    plt.show()

if __name__ == "__main__":
    main()
