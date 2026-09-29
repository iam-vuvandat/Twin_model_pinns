import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_network_diagram():
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.axis('off')
    
    # Hàm hỗ trợ vẽ các khối hộp
    def draw_box(x, y, width, height, text, facecolor, edgecolor, fontsize=10):
        box = patches.FancyBboxPatch((x, y), width, height, boxstyle="round,pad=0.1", 
                                     edgecolor=edgecolor, facecolor=facecolor, lw=2)
        ax.add_patch(box)
        ax.text(x + width/2, y + height/2, text, ha='center', va='center', 
                fontsize=fontsize, fontweight='bold', color='black')
        return (x + width/2, y), (x + width/2, y + height), (x, y + height/2), (x + width, y + height/2)

    # Hàm hỗ trợ vẽ mũi tên
    def draw_arrow(start, end, rad=0.0):
        ax.annotate('', xy=end, xytext=start,
                    arrowprops=dict(arrowstyle="->", color='black', lw=2, 
                                    connectionstyle=f"arc3,rad={rad}"))

    # Vẽ nền cho khu vực Mạng nơ-ron
    network_bg = patches.Rectangle((1.5, 6.5), 11, 2.5, linewidth=2, edgecolor='gray', 
                                   facecolor='#f5f5f5', linestyle='dashed')
    ax.add_patch(network_bg)
    ax.text(7, 8.8, "PARALLEL MULTI-NETWORK ARCHITECTURE", ha='center', va='center', fontsize=12, fontweight='bold', color='gray')

    # Khối 1: Inputs
    _, in_top, _, _ = draw_box(5.5, 10.5, 3, 1, "Inputs:\n(x, y, d_gap)", '#e8f5e9', '#2e7d32', 12)
    in_bottom = (7, 10.5)
    
    # Khối 2: Mạng hình học (Trái)
    geo_bottom, geo_top, _, _ = draw_box(2.5, 7, 4, 1.5, "Geometry Sub-Network\n(MLP: 3 layers x 64)\nOutput: Sigmoid", '#e3f2fd', '#1565c0')
    
    # Khối 3: Mạng vật lý (Phải)
    phys_bottom, phys_top, _, _ = draw_box(7.5, 7, 4, 1.5, "Physics Main-Network\n(MLP: 6 layers x 128)\nOutput: Linear", '#e3f2fd', '#1565c0')

    # Khối 4: Outputs
    mask_bottom, mask_top, _, _ = draw_box(2.5, 4.5, 4, 1, "Magnetization Mask\nM_x(x, y, d_gap)", '#fff3e0', '#e65100')
    field_bottom, field_top, _, _ = draw_box(7.5, 4.5, 4, 1, "Electromagnetic Fields\n(A_z, B_x, B_y)", '#fff3e0', '#e65100')

    # Khối 5: PyTorch Autograd
    _, auto_top, _, _ = draw_box(5.5, 2.5, 3, 1, "PyTorch Autograd\n(Spatial Derivatives)", '#f3e5f5', '#6a1b9a')
    auto_bottom = (7, 2.5)

    # Khối 6: PDE Loss
    loss_bottom, loss_top, _, _ = draw_box(4.5, 0.5, 5, 1, "PDE Loss Function\n(Ampere's Law, Gauss's Law)", '#ffebee', '#c62828')

    # Vẽ kết nối (Arrows)
    # Inputs -> Networks
    draw_arrow(in_bottom, (4.5, geo_top[1]), rad=0.2)
    draw_arrow(in_bottom, (9.5, phys_top[1]), rad=-0.2)
    
    # Networks -> Outputs
    draw_arrow(geo_bottom, mask_top)
    draw_arrow(phys_bottom, field_top)
    
    # Outputs -> Autograd
    draw_arrow(mask_bottom, (6.5, auto_top[1]), rad=-0.2)
    draw_arrow(field_bottom, (7.5, auto_top[1]), rad=0.2)
    
    # Autograd -> Loss
    draw_arrow(auto_bottom, loss_top)

    # Cập nhật trọng số (Backpropagation)
    ax.annotate('', xy=(1, 7.75), xytext=(4.5, 1.0),
                arrowprops=dict(arrowstyle="->", color='red', lw=2, linestyle='dashed',
                                connectionstyle="angle,angleA=180,angleB=90,rad=10"))
    ax.text(2.5, 1.5, "Backpropagation\n(Update Weights)", color='red', fontweight='bold', ha='center')

    plt.title("Parametric PINN with Geometry Sub-Network", fontsize=16, fontweight='bold', pad=20)
    plt.xlim(0, 14)
    plt.ylim(-0.5, 12)
    plt.tight_layout()
    
    # Lưu và hiển thị ảnh
    file_name = "multi_network_pinn_architecture.png"
    plt.savefig(file_name, dpi=300)
    print(f"Diagram saved as {file_name}")
    plt.show()

if __name__ == "__main__":
    draw_network_diagram()