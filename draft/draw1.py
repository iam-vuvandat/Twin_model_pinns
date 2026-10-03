import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def draw_4_material_pinn():
    # Khởi tạo khung hình tỷ lệ rộng
    fig, ax = plt.subplots(figsize=(16, 11))
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 11)
    ax.axis('off')

    # Bảng màu Pastel trực quan
    c_nn_fill, c_nn_edge = '#E1F5FE', '#0288D1'   # Xanh dương: Khối Học máy
    c_phy_fill, c_phy_edge = '#F1F8E9', '#689F38' # Xanh lá: Khối Vật lý & Hình học
    c_out_fill, c_out_edge = '#FFF3E0', '#F57C00' # Cam: Khối Đầu ra

    def add_box(x, y, w, h, text, fill, edge):
        """Hàm vẽ hộp bo góc và văn bản bên trong"""
        box = mpatches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2", 
                                      fc=fill, ec=edge, lw=2.5, zorder=3)
        ax.add_patch(box)
        ax.text(x + w/2, y + h/2, text, ha='center', va='center', 
                fontsize=10, fontweight='bold', color='#263238', zorder=4)
        return {'N': (x+w/2, y+h), 'S': (x+w/2, y), 'E': (x+w, y+h/2), 'W': (x, y+h/2)}

    # Kích thước một node
    w, h = 2.8, 1.2
    nodes = {}
    
    # 1. CỘT 1 & 2: Đầu vào và Khối trích xuất chung
    nodes['Input'] = add_box(0.5, 4.5, w, h, "Tọa độ (x, y)\nĐiểm cần tính toán", c_nn_fill, c_nn_edge)
    nodes['Common'] = add_box(4.0, 4.5, w, h, "Khối trích xuất chung\nz = N(x)\n(Backbone)", c_nn_fill, c_nn_edge)
    
    # 2. CỘT 3: Các nhánh Chuyên gia (Song song)
    nodes['SDF']   = add_box(8.0, 9.0, w, h, "Trọng tài Hình học\n(Tính 4 Mask H_i từ SDF)", c_phy_fill, c_phy_edge)
    nodes['Air']   = add_box(8.0, 7.0, w, h, "Nhánh 1: Không khí\nTính f_air", c_nn_fill, c_nn_edge)
    nodes['Mag']   = add_box(8.0, 5.0, w, h, "Nhánh 2: Nam châm\nTính f_mag", c_nn_fill, c_nn_edge)
    nodes['Iron']  = add_box(8.0, 3.0, w, h, "Nhánh 3: Lõi Sắt\nTính f_iron", c_nn_fill, c_nn_edge)
    nodes['Cop']   = add_box(8.0, 1.0, w, h, "Nhánh 4: Cuộn Đồng\nTính f_copper", c_nn_fill, c_nn_edge)
    
    # 3. CỘT 4 & 5: Gộp nghiệm và Đầu ra
    nodes['Merge'] = add_box(12.5, 4.5, w, h, "Hợp nhất nghiệm\nf = Σ (Mask_i × f_i)", c_out_fill, c_out_edge)
    nodes['Bound'] = add_box(12.5, 1.0, w, h, "Hàm biên d(x)\n(Ép nghiệm = 0 ở rìa)", c_phy_fill, c_phy_edge)
    nodes['Output']= add_box(16.5, 4.5, w-0.5, h, "Dự đoán\nA_z", c_out_fill, c_out_edge)

    def add_arrow(pt1, pt2, rad=0.0, text=None, text_offset=(0, 0)):
        """Hàm vẽ mũi tên uốn lượn"""
        arrow = mpatches.FancyArrowPatch(
            pt1, pt2, connectionstyle=f"arc3,rad={rad}", 
            arrowstyle="->,head_length=6,head_width=4", 
            lw=2, color='#546E7A', shrinkA=4, shrinkB=4, zorder=2)
        ax.add_patch(arrow)
        if text:
            mx, my = (pt1[0]+pt2[0])/2, (pt1[1]+pt2[1])/2
            ax.text(mx + text_offset[0], my + text_offset[1], text, ha='center', fontsize=9, 
                    color='#D84315', fontweight='bold', 
                    bbox=dict(facecolor='#ffffff', edgecolor='none', alpha=0.9, pad=1), zorder=5)

    # --- KẾT NỐI CÁC KHỐI ---
    # Đầu vào -> Khối chung, SDF và Biên
    add_arrow(nodes['Input']['E'], nodes['Common']['W'])
    add_arrow(nodes['Input']['N'], nodes['SDF']['W'], rad=0.15)
    add_arrow(nodes['Input']['S'], nodes['Bound']['W'], rad=-0.2)
    
    # Khối chung -> 4 Nhánh chuyên gia
    add_arrow(nodes['Common']['E'], nodes['Air']['W'], rad=0.2)
    add_arrow(nodes['Common']['E'], nodes['Mag']['W'], rad=0.1)
    add_arrow(nodes['Common']['E'], nodes['Iron']['W'], rad=-0.1)
    add_arrow(nodes['Common']['E'], nodes['Cop']['W'], rad=-0.2)
    
    # 4 Nhánh -> Gộp nghiệm
    add_arrow(nodes['Air']['E'], nodes['Merge']['W'], rad=-0.2)
    add_arrow(nodes['Mag']['E'], nodes['Merge']['W'], rad=-0.1)
    add_arrow(nodes['Iron']['E'], nodes['Merge']['W'], rad=0.1)
    add_arrow(nodes['Cop']['E'], nodes['Merge']['W'], rad=0.2)
    
    # Trọng tài hình học -> Cung cấp Mask cho Gộp nghiệm
    add_arrow(nodes['SDF']['E'], nodes['Merge']['N'], rad=-0.3, 
              text="Cung cấp 4 Mặt nạ\n(Mask_air, Mask_mag,...)", text_offset=(-0.5, 0.8))
    
    # Ép biên và xuất kết quả
    add_arrow(nodes['Merge']['E'], nodes['Output']['W'])
    add_arrow(nodes['Bound']['E'], nodes['Output']['S'], rad=0.2, 
              text="Nhân điều kiện biên", text_offset=(0.2, -0.6))
    
    # --- TRANG TRÍ ---
    plt.title("SƠ ĐỒ KIẾN TRÚC MẠNG PINN 4 VẬT LIỆU (MIXTURE OF EXPERTS)", 
              fontsize=16, fontweight='900', color='#1565C0', pad=10)
    
    # Legend
    handles = [
        mpatches.Patch(facecolor=c_nn_fill, edgecolor=c_nn_edge, lw=2, label='Mạng Nơ-ron (Tự động học)'),
        mpatches.Patch(facecolor=c_phy_fill, edgecolor=c_phy_edge, lw=2, label='Vật lý / Hình học (SDF)'),
        mpatches.Patch(facecolor=c_out_fill, edgecolor=c_out_edge, lw=2, label='Đầu ra Hợp nhất')
    ]
    ax.legend(handles=handles, loc='upper right', fontsize=11, framealpha=1, shadow=True)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    draw_4_material_pinn()