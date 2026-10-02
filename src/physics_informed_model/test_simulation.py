import os
import sys

current_directory = os.path.dirname(os.path.abspath(__file__))
if current_directory not in sys.path:
    sys.path.insert(0, current_directory)

import torch
import numpy as np
import matplotlib.pyplot as plt
from geometry_engine.geometry import Geometry
from geometry_engine.segment.segment import Segment
from physics_domain.collocation_sampler import CollocationSampler
from electro_magnetic_pinn import ElectroMagneticPINN

def main():
    geometry_instance = Geometry()
    
    # 1. Nam châm chữ I nằm ngang (Phía trên)
    # Kích thước: Rộng 0.06m, Dày 0.01m. Tâm tại y = 0.02
    top_magnet_vertices = [
        [-0.03, 0.015],
        [0.03, 0.015],
        [0.03, 0.025],
        [-0.03, 0.025]
    ]
    top_magnet = Segment(top_magnet_vertices).set_material_properties(
        name="top_magnet",
        relative_permeability=1.05,
        coercive_field_x=800000.0,  # Từ hóa hướng sang phải (+X)
        coercive_field_y=0.0
    )
    geometry_instance.add_segment(top_magnet)

    # 2. Nam châm chữ I nằm ngang (Phía dưới)
    # Kích thước: Rộng 0.06m, Dày 0.01m. Tâm tại y = -0.02
    bottom_magnet_vertices = [
        [-0.03, -0.025],
        [0.03, -0.025],
        [0.03, -0.015],
        [-0.03, -0.015]
    ]
    bottom_magnet = Segment(bottom_magnet_vertices).set_material_properties(
        name="bottom_magnet",
        relative_permeability=1.05,
        coercive_field_x=-800000.0, # Từ hóa hướng sang trái (-X)
        coercive_field_y=0.0
    )
    geometry_instance.add_segment(bottom_magnet)
    
    collocation_sampler_instance = CollocationSampler(
        x_boundaries_tuple=(-0.05, 0.05),
        y_boundaries_tuple=(-0.05, 0.05)
    )
    
    # ---------------------------------------------------------
    # TRỰC QUAN HÓA HÌNH HỌC TRƯỚC KHI HUẤN LUYỆN
    # ---------------------------------------------------------
    resolution = 100
    x_coords = np.linspace(-0.05, 0.05, resolution)
    y_coords = np.linspace(-0.05, 0.05, resolution)
    X_grid, Y_grid = np.meshgrid(x_coords, y_coords)
    
    xy_points_tensor = torch.tensor(np.column_stack((X_grid.ravel(), Y_grid.ravel())), dtype=torch.float32)
    sdf_values_tensor = geometry_instance.compute_global_signed_distance_field(xy_points_tensor)
    
    sdf_grid_np = sdf_values_tensor.numpy().reshape(resolution, resolution)
    
    plt.figure(figsize=(7, 6))
    contour_plot = plt.contourf(X_grid, Y_grid, sdf_grid_np, levels=50, cmap="coolwarm")
    plt.colorbar(contour_plot, label="Signed Distance Field (SDF)")
    plt.contour(X_grid, Y_grid, sdf_grid_np, levels=[0.0], colors="black", linewidths=2.5)
    
    plt.title("Geometry Definition: Two Horizontal Magnets")
    plt.xlabel("x position (m)")
    plt.ylabel("y position (m)")
    plt.axis("equal")
    plt.tight_layout()
    plt.show()
    # ---------------------------------------------------------

    model = ElectroMagneticPINN(
        geometry_engine_instance=geometry_instance,
        collocation_sampler_instance=collocation_sampler_instance
    )
    
    model.execute_training_process(
        number_of_uniform_points=200,
        number_of_interface_points=50,
        distance_threshold=0.005,
        stages=2,
        epochs_per_stage=5
    )
    
    test_points = collocation_sampler_instance.generate_uniform_points_tensor(10)
    predictions = model.predict_magnetic_vector_potential(test_points)
    print("Predicted A_z:\n", predictions)

if __name__ == '__main__':
    main()
