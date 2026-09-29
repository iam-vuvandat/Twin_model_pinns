import torch
import numpy as np
import matplotlib.pyplot as plt

def smooth_maximum(d1, d2, k=15.0):
    """
    Phép toán Smooth Union / Maximum khả vi hoàn toàn cho SDF.
    Dùng để hợp nhất các khối hình học lại với nhau một cách mượt mà.
    """
    exp_term = torch.exp(k * d1) + torch.exp(k * d2)
    return torch.log(torch.clamp(exp_term, min=1.0e-12)) / k

def signed_distance_rectangle(xy, width, height, center):
    """
    Hàm khoảng cách có hướng (SDF) tiền định cho hình chữ nhật.
    """
    pos = xy - center
    d = torch.abs(pos) - torch.tensor([width / 2.0, height / 2.0], device=xy.device)
    outside_dist = torch.norm(torch.clamp(d, min=0.0), dim=1)
    inside_dist = torch.min(torch.max(d[:, 0], d[:, 1]), torch.tensor(0.0, device=xy.device))
    return outside_dist + inside_dist

def compute_deterministic_geometry(xy, d_gap):
    """
    Định nghĩa hình học tiền định: Gông sắt hình chữ nhật ở giữa 
    và 2 khối nam châm dịch chuyển theo khoảng cách d_gap.
    """
    # 1. Gông sắt ở giữa (Hình chữ nhật)
    d_rect = signed_distance_rectangle(xy, width=1.2, height=0.3, center=torch.tensor([0.0, 0.0], device=xy.device))
    
    # 2. Hai khối nam châm dịch chuyển theo d_gap
    mag_top_center = torch.tensor([0.0, 0.25 + d_gap / 2.0], device=xy.device)
    mag_bot_center = torch.tensor([0.0, -0.25 - d_gap / 2.0], device=xy.device)
    
    d_mag1 = signed_distance_rectangle(xy, width=0.8, height=0.3, center=mag_top_center)
    d_mag2 = signed_distance_rectangle(xy, width=0.8, height=0.3, center=mag_bot_center)
    
    # 3. Hợp nhất mượt mà các khối bằng Smooth Maximum
    combined_magnets = smooth_maximum(d_mag1, d_mag2, k=20.0)
    final_shape = smooth_maximum(d_rect, combined_magnets, k=15.0)
    
    return final_shape

if __name__ == "__main__":
    resolution = 300
    x = np.linspace(-1.5, 1.5, resolution)
    y = np.linspace(-1.5, 1.5, resolution)
    X, Y = np.meshgrid(x, y)
    
    xy_np = np.column_stack((X.ravel(), Y.ravel()))
    xy_tensor = torch.tensor(xy_np, dtype=torch.float32, requires_grad=True)
    
    # Thử nghiệm với khoảng cách d_gap = 0.5 mm
    d_gap_value = 0.5
    
    # Tính toán hình học tiền định
    sdf_values = compute_deterministic_geometry(xy_tensor, d_gap=d_gap_value)
    
    # Kiểm tra tính khả vi tự động qua PyTorch Autograd
    dummy_loss = torch.sum(sdf_values)
    dummy_loss.backward()
    print("[INFO] Đạo hàm không gian khả vi hoàn toàn với hàm tiền định!")
    
    # Trực quan hóa
    SDF_grid = sdf_values.detach().numpy().reshape(X.shape)
    
    plt.figure(figsize=(8, 8))
    contour = plt.contourf(X, Y, SDF_grid, levels=60, cmap="viridis")
    plt.colorbar(contour, label="Deterministic SDF / Mask")
    plt.title(f"Deterministic Smooth CSG Geometry (d_gap = {d_gap_value})", fontsize=14, fontweight='bold')
    plt.xlabel("x (m)")
    plt.ylabel("y (m)")
    plt.axis("equal")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()