import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def draw_pinn_architecture():
    # Khởi tạo khung hình với kích thước lớn và loại bỏ trục tọa độ
    fig, ax = plt.subplots(figsize=(15, 9))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis('off')

    # Định nghĩa bảng màu (Pastel đẹp mắt)
    c_nn_fill, c_nn_edge = '#E1F5FE', '#0288D1'   # Xanh dương cho khối Nơ-ron
    c_phy_fill, c_phy_edge = '#F1F8E9', '#689F38' # Xanh lá cho khối Vật lý/Hình học
    c_out_fill, c_out_edge = '#FFF3E0', '#F57C00' # Cam cho khối Đầu ra

    # Hàm hỗ trợ vẽ các hình chữ nhật bo góc
    def add_box(x, y, w, h, text, fill, edge):
        box = mpatches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2", 
                                      fc=fill, ec=edge, lw=2.5)
        ax.add_patch(box)
        ax.text(x + w/2, y + h/2, text, ha='center', va='center', 
                fontsize=11, fontweight='bold', color='#263238')
        # Trả về các điểm neo để vẽ mũi tên (Bắc, Nam, Đông, Tây)
        return {'N': (x+w/2, y+h), 'S': (x+w/2, y), 'E': (x+w, y+h/2), 'W': (x, y+h/2)}

    # Kích thước chuẩn của một khối
    b_w, b_h = 2.8, 1.2
    nodes = {}
    
    # 1. Các khối Tọa độ & Mạng Nơ-ron (Dữ liệu học máy)
    nodes['Input'] = add_box(0.5, 4, b_w, b_h, "Tọa độ đầu vào\n(x, y)", c_nn_fill, c_nn_edge)
    nodes['Common'] = add_box(4.5, 4, b_w, b_h, "Khối chung: z = N(x)\n(Đặc trưng tổng quát)", c_nn_fill, c_nn_edge)
    nodes['B1'] = add_box(8.5, 5.5, b_w, b_h, "Nhánh 1: f₁(z)\n(Môi trường Không khí)", c_nn_fill, c_nn_edge)
    nodes['B2'] = add_box(8.5, 2.5, b_w, b_h, "Nhánh 2: f₂(z)\n(Lõi Nam châm)", c_nn_fill, c_nn_edge)
    
    # 2. Các khối Hình học & Vật lý
    nodes['SDF'] = add_box(4.5, 7.5, b_w, b_h, "Trường SDF\n(Tính khoảng cách)", c_phy_fill, c_phy_edge)
    nodes['H'] = add_box(8.5, 7.5, b_w, b_h, "Heaviside mượt: Ĥ\n(Hệ số mask_smooth)", c_phy_fill, c_phy_edge)
    nodes['Bound'] = add_box(8.5, 0.5, b_w, b_h, "Hàm biên d(x)\n(boundary_factor)", c_phy_fill, c_phy_edge)
    
    # 3. Các khối Gộp & Đầu ra
    nodes['Merge'] = add_box(12.5, 4, b_w, b_h, "Nội suy vật liệu\nf = f₁ + Ĥ × f₂", c_out_fill, c_out_edge)
    nodes['Out'] = add_box(12.5, 1.5, b_w, b_h, "Thế vector từ (A_z)\nA_z = f × d(x)", c_out_fill, c_out_edge)

    # Hàm hỗ trợ vẽ mũi tên uốn lượn
    def add_arrow(pt1, pt2, connectionstyle="arc3,rad=0", text=None, text_offset_y=0.2):
        arrow = mpatches.FancyArrowPatch(pt1, pt2, connectionstyle=connectionstyle, 
                                         arrowstyle="->,head_length=8,head_width=5", 
                                         lw=2, color='#546E7A', shrinkA=5, shrinkB=5)
        ax.add_patch(arrow)
        if text:
            mx, my = (pt1[0]+pt2[0])/2, (pt1[1]+pt2[1])/2
            ax.text(mx, my + text_offset_y, text, ha='center', fontsize=9, 
                    color='#D84315', fontweight='bold', 
                    bbox=dict(facecolor='white', edgecolor='none', alpha=0.8, pad=1))

    # --- Vẽ các kết nối (Mũi tên) ---
    
    # Từ Input chia ra 3 hướng
    add_arrow(nodes['Input']['E'], nodes['Common']['W'])
    add_arrow(nodes['Input']['N'], nodes['SDF']['W'], connectionstyle="arc3,rad=0.2")
    add_arrow(nodes['Input']['S'], nodes['Bound']['W'], connectionstyle="arc3,rad=-0.15")
    
    # Từ Khối chung tẽ ra 2 nhánh vật liệu
    add_arrow(nodes['Common']['E'], nodes['B1']['W'], connectionstyle="arc3,rad=0.2")
    add_arrow(nodes['Common']['E'], nodes['B2']['W'], connectionstyle="arc3,rad=-0.2")
    
    # Từ SDF tính ra Heaviside
    add_arrow(nodes['SDF']['E'], nodes['H']['W'])
    
    # Gộp 2 nhánh vào khối Nội suy
    add_arrow(nodes['B1']['E'], nodes['Merge']['W'], connectionstyle="arc3,rad=-0.2")
    add_arrow(nodes['B2']['E'], nodes['Merge']['W'], connectionstyle="arc3,rad=0.2")
    
    # Heaviside truyền tỷ lệ xuống khối Nội suy
    add_arrow(nodes['H']['S'], nodes['Merge']['N'], connectionstyle="arc3,rad=-0.3", text="Hệ số tỷ lệ nội suy", text_offset_y=0.6)
    
    # Ép điều kiện biên để ra kết quả cuối cùng
    add_arrow(nodes['Merge']['S'], nodes['Out']['N'])
    add_arrow(nodes['Bound']['E'], nodes['Out']['S'], connectionstyle="arc3,rad=0.3", text="Ép điều kiện biên", text_offset_y=-0.5)
    
    # Thêm tiêu đề
    plt.title("SƠ ĐỒ KIẾN TRÚC MẠNG PINN PHÂN NHÁNH VẬT LIỆU", 
              fontsize=18, fontweight='900', color='#1565C0', pad=20)
    
    # Thêm chú thích
    legend_elements = [
        mpatches.Patch(facecolor=c_nn_fill, edgecolor=c_nn_edge, lw=2, label='Mạng Nơ-ron (Học máy)'),
        mpatches.Patch(facecolor=c_phy_fill, edgecolor=c_phy_edge, lw=2, label='Hình học & Vật lý'),
        mpatches.Patch(facecolor=c_out_fill, edgecolor=c_out_edge, lw=2, label='Đầu ra (Dự đoán)')
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=11, frameon=True, shadow=True)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    draw_pinn_architecture()