import torch
import numpy as np
import matplotlib.pyplot as plt

def signed_distance_rectangle(xy, width, height, center):
    pos = xy - center
    d = torch.abs(pos) - torch.tensor([width / 2.0, height / 2.0], device=xy.device)
    outside_dist = torch.norm(torch.clamp(d, min=0.0), dim=1)
    inside_dist = torch.min(torch.max(d[:, 0], d[:, 1]), torch.tensor(0.0, device=xy.device))
    return outside_dist + inside_dist

def signed_distance_circle(xy, radius, center):
    return torch.norm(xy - center, dim=1) - radius

if __name__ == "__main__":
    resolution = 400
    x = np.linspace(-2.0, 2.0, resolution)
    y = np.linspace(-2.0, 2.0, resolution)
    X, Y = np.meshgrid(x, y)
    
    xy_np = np.column_stack((X.ravel(), Y.ravel()))
    xy_tensor = torch.tensor(xy_np, dtype=torch.float32)
    
    center_rect = torch.tensor([0.0, 0.0], dtype=torch.float32)
    sdf_rect = signed_distance_rectangle(xy_tensor, width=2.0, height=1.0, center=center_rect)
    SDF_rect_grid = sdf_rect.numpy().reshape(resolution, resolution)
    
    center_circle = torch.tensor([0.0, 0.0], dtype=torch.float32)
    sdf_circle = signed_distance_circle(xy_tensor, radius=1.0, center=center_circle)
    SDF_circle_grid = sdf_circle.numpy().reshape(resolution, resolution)
    
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    contour_rect = axes[0].contourf(X, Y, SDF_rect_grid, levels=60, cmap="coolwarm")
    axes[0].contour(X, Y, SDF_rect_grid, levels=[0.0], colors="black", linewidths=2.5)
    axes[0].set_title("SDF: Rectangle (2.0 x 1.0)")
    axes[0].set_xlabel("x")
    axes[0].set_ylabel("y")
    axes[0].set_aspect("equal")
    fig.colorbar(contour_rect, ax=axes[0], label="Distance")
    
    contour_circle = axes[1].contourf(X, Y, SDF_circle_grid, levels=60, cmap="coolwarm")
    axes[1].contour(X, Y, SDF_circle_grid, levels=[0.0], colors="black", linewidths=2.5)
    axes[1].set_title("SDF: Circle (R = 1.0)")
    axes[1].set_xlabel("x")
    axes[1].set_ylabel("y")
    axes[1].set_aspect("equal")
    fig.colorbar(contour_circle, ax=axes[1], label="Distance")
    
    plt.tight_layout()
    plt.show()