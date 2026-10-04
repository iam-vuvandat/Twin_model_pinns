import os

def execute_expand_box():
    base_directory = os.path.dirname(os.path.abspath(__file__))
    project_root_directory = os.path.abspath(os.path.join(base_directory, '..'))
    
    target_file_path = os.path.join(project_root_directory, 'test_simulation.py')
    
    new_code = """\"\"\"
version 2.1.0 - Expanded Bounding Box (-0.08 to 0.08)
\"\"\"
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
    # 1. KHỞI TẠO HÌNH HỌC 
    geometry_instance = Geometry(steepness=5000.0)
    
    # --- VẬT THỂ 1: THANH SẮT TỪ ---
    iron_bar_vertices = [
        [-0.04, 0.02],
        [ 0.04, 0.02],
        [ 0.04, 0.03],
        [-0.04, 0.03]
    ]
    iron_bar = Segment(iron_bar_vertices).set_material_properties(
        name="iron", 
        relative_permeability=2000.0, 
        coercive_field_x=0.0,
        coercive_field_y=0.0
    )
    geometry_instance.add_segment(iron_bar)

    # --- VẬT THỂ 2: NAM CHÂM CHỮ U ---
    magnet_u_vertices = [
        [-0.04, 0.01],
        [-0.02, 0.01],
        [-0.02, -0.02],
        [ 0.02, -0.02],
        [ 0.02, 0.01],
        [ 0.04, 0.01],
        [ 0.04, -0.04],
        [-0.04, -0.04]
    ]
    magnet_u_shape = Segment(magnet_u_vertices).set_material_properties(
        name="magnet",
        relative_permeability=1.05,
        coercive_field_x=0.0,
        coercive_field_y=800000.0
    )
    geometry_instance.add_segment(magnet_u_shape)
    
    # 2. KHỞI TẠO BỘ LẤY MẪU (MỞ RỘNG KHÔNG GIAN)
    collocation_sampler_instance = CollocationSampler(
        x_boundaries_tuple=(-0.08, 0.08),
        y_boundaries_tuple=(-0.08, 0.08)
    )

    print("Vẽ sơ đồ bài toán hình học...")
    geometry_instance.plot_problem_definition(
        x_boundaries_tuple=(-0.08, 0.08),
        y_boundaries_tuple=(-0.08, 0.08),
        resolution=150
    )

    # 3. CẤU HÌNH MẠNG NƠ-RON HỖN HỢP CHUYÊN GIA
    model = ElectroMagneticPINN(
        geometry_engine_instance=geometry_instance,
        collocation_sampler_instance=collocation_sampler_instance,
        hidden_layers=5,               
        hidden_neurons=64,             
        activation_function=nn.Tanh(),
        use_fourier=True,              
        fourier_features=64,           
        fourier_scale=1.5              
    )
    
    # 4. TIẾN HÀNH HUẤN LUYỆN
    print("Bắt đầu huấn luyện mạng PINN phân nhánh...")
    model.execute_training_process(
        number_of_uniform_points=3500,   # Tăng nhẹ số điểm lấy mẫu vì không gian lớn hơn
        number_of_interface_points=1200,
        distance_threshold=0.005,
        epochs_adam=1200,                
        epochs_lbfgs=200                 
    )
    
    # 5. ĐÁNH GIÁ VÀ TRỰC QUAN HÓA (CẬP NHẬT TỌA ĐỘ LƯỚI)
    print("Đang tạo biểu đồ trực quan hóa kết quả trường điện từ...")
    resolution = 120
    x_coords = np.linspace(-0.08, 0.08, resolution)
    y_coords = np.linspace(-0.08, 0.08, resolution)
    X_grid, Y_grid = np.meshgrid(x_coords, y_coords)
    
    xy_points_tensor = torch.tensor(np.column_stack((X_grid.ravel(), Y_grid.ravel())), dtype=torch.float32)
    
    A_z_pred, B_x_pred, B_y_pred = model.evaluate_fields(xy_points_tensor)
    
    A_z_grid = A_z_pred.numpy().reshape(resolution, resolution)
    B_x_grid = B_x_pred.numpy().reshape(resolution, resolution)
    B_y_grid = B_y_pred.numpy().reshape(resolution, resolution)
    B_mag_grid = np.sqrt(B_x_grid**2 + B_y_grid**2)
    
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
    
    fig2, ax2 = plt.subplots(figsize=(8, 7))
    contour_b_bg = ax2.contourf(X_grid, Y_grid, B_mag_grid, levels=60, cmap="rainbow", alpha=0.4)
    fig2.colorbar(contour_b_bg, ax=ax2, label="|B| (T)")
    
    step = 4
    X_sub = X_grid[::step, ::step]
    Y_sub = Y_grid[::step, ::step]
    Bx_sub = B_x_grid[::step, ::step]
    By_sub = B_y_grid[::step, ::step]
    
    ax2.quiver(X_sub, Y_sub, Bx_sub, By_sub, color='black', pivot='mid')
    
    ax2.set_title("Magnetic Flux Density Vectors (B)")
    ax2.set_xlabel("x (m)")
    ax2.set_ylabel("y (m)")
    ax2.set_aspect('equal')
    
    fig2.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
"""
    
    with open(target_file_path, 'w', encoding='utf-8') as f:
        f.write(new_code)
        
    print(f"Hoàn tất: Không gian mô phỏng trong tệp {target_file_path} đã được mở rộng thành ±0.08.")

if __name__ == "__main__":
    execute_expand_box()