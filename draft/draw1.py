import torch
import numpy as np
import matplotlib.pyplot as plt

def smooth_minimum(d1, d2, k=10.0):
    """
    Phép toán Smooth Union (Exponential Smooth Minimum) khả vi hoàn toàn.
    Thay thế cho lệnh if-else hoặc min() cứng nhắc.
    """
    # Tránh tràn số mũ (overflow/underflow) bằng cách tách giá trị
    # Hoặc dùng công thức log-sum-exp chuẩn
    exp_term = torch.exp(-k * d1) + torch.exp(-k * d2)
    return -torch.log(torch.clamp(exp_term, min=1.0e-12)) / k

def signed_distance_rectangle(xy, width, height, center):
    """
    Hàm khoảng cách có hướng (SDF) cho hình chữ nhật.
    xy: Tensor tọa độ (N, 2)
    width, height: Kích thước hình chữ nhật
    center: Tọa độ tâm (x, y)
    """
    pos = xy - center
    d = torch.abs(pos) - torch.tensor([width / 2.0, height / 2.0], device=xy.device)
    # Khoảng cách bên ngoài cộng với khoảng cách bên trong
    outside_dist = torch.norm(torch.clamp(d, min=0.0), dim=1)
    inside_dist = torch.min(torch.max(d[:, 0], d[:, 1]), torch.tensor(0.0, device=xy.device))
    return outside_dist + inside_dist

def signed_distance_circle(xy, radius, center):
    """
    Hàm khoảng cách có hướng (SDF) cho hình tròn.
    """
    return radius - torch.norm(xy - center, dim=1)

def compute_differentiable_geometry(xy, d_gap):
    """
    Ghép nối hình học: Một hình chữ nhật (gông sắt) và hai hình tròn (nam châm) 
    cách nhau một khoảng d_gap theo trục y, hoàn toàn khả vi qua PyTorch.
    """
    # Tâm hình chữ nhật
    rect_center = torch.tensor([0.0, 0.0], device=xy.device)
    d_rect = signed_distance_rectangle(xy, width=1.0, height=0.4, center=rect_center)
    
    # Tâm 2 nam châm dịch chuyển theo khoảng cách d_gap
    magnet_top_center = torch.tensor([0.0, 0.2 + d_gap / 2.0], device=xy.device)
    magnet_bot_center = torch.tensor([0.0, -0.2 - d_gap / 2.0], device=xy.device)
    
    d_mag1 = signed_distance_circle(xy, radius=0.25, center=magnet_top_center)
    d_mag2 = signed_distance_circle(xy, radius=0.25, center=magnet_bot_center)
    
    # Ghép mượt mà các khối bằng Smooth Minimum (Differentiable CSG)
    combined_magnets = smooth_minimum(d_mag1, d_mag2, k=15.0)
    final_shape = smooth_minimum(d_rect, combined_magnets, k=10.0)
    
    return final_shape

if __name__ == "__main__":
    # 1. Tạo lưới không gian 2D để kiểm tra
    resolution = 200
    x = np.linspace(-1.5, 1.5, resolution)
    y = np.linspace(-1.5, 1.5, resolution)
    X, Y = np.meshgrid(x, y)
    
    # Chuyển đổi thành PyTorch Tensor và bật requires_grad để kiểm tra tính khả vi
    xy_np = np.column_stack((X.ravel(), Y.ravel()))
    xy_tensor = torch.tensor(xy_np, dtype=torch.float32, requires_grad=True)
    
    # Giả sử khoảng cách d_gap giữa 2 nam châm là 0.4 mm
    d_gap_value = 0.4
    
    # 2. Tính toán hàm hình học khả vi
    sdf_values = compute_differentiable_geometry(xy_tensor, d_gap=d_gap_value)
    
    # 3. Kiểm tra tính khả vi bằng cách tính đạo hàm không gian tự động (PyTorch Autograd)
    # Đây chính là cơ chế cốt lõi để đưa vào phương trình Maxwell trong PINN
    dummy_loss = torch.sum(sdf_values)
    dummy_loss.backward()
    
    print("[INFO] Đạo hàm không gian (Grad) đã được tính toán thành công qua PyTorch Autograd!")
    print(f"[INFO] Kích thước gradient kiểm tra: {xy_tensor.grad.shape}")
    
    # 4. Trực quan hóa hình học mượt mà
    SDF_grid = sdf_values.detach().numpy().reshape(X.shape)
    
    plt.figure(figsize=(8, 8))
    contour = plt.contourf(X, Y, SDF_grid, levels=50, cmap="coolwarm")
    plt.colorbar(contour, label="SDF / Material Mask Value")
    plt.title(f"Differentiable CSG Geometry (d_gap = {d_gap_value})", fontsize=14, fontweight='bold')
    plt.xlabel("x (m)")
    plt.ylabel("y (m)")
    plt.axis("equal")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()