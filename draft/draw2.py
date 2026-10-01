import numpy
import matplotlib.pyplot
import matplotlib.animation

def generate_pinn_training_animation():
    """
    Tạo tệp GIF minh họa 5 bước huấn luyện của Mạng Nơ-ron Thông tin Vật lý (PINN).
    """
    # Khởi tạo dữ liệu không gian
    spatial_resolution = 100
    x_coordinates_array = numpy.linspace(-2.0, 2.0, spatial_resolution)
    y_coordinates_array = numpy.linspace(-2.0, 2.0, spatial_resolution)
    x_mesh_grid, y_mesh_grid = numpy.meshgrid(x_coordinates_array, y_coordinates_array)

    # Tạo một hàm mô phỏng nghiệm vật lý thực tế (Mô phỏng từ trường lưỡng cực)
    radius_squared = x_mesh_grid**2 + y_mesh_grid**2
    true_magnetic_vector_potential = numpy.exp(-radius_squared) * numpy.cos(numpy.pi * x_mesh_grid / 2.0)
    
    # Ép điều kiện biên Dirichlet bằng 0 ở rìa
    boundary_mask = (numpy.abs(x_mesh_grid) < 1.9) & (numpy.abs(y_mesh_grid) < 1.9)
    true_magnetic_vector_potential = true_magnetic_vector_potential * boundary_mask

    # Thiết lập khung hình đồ thị
    figure_object, axes_array = matplotlib.pyplot.subplots(nrows=2, ncols=2, figsize=(12, 10))
    figure_object.suptitle("Quy Trình Huấn Luyện Mạng Nơ-ron Thông tin Vật lý (PINN)", fontsize=16)

    total_animation_frames = 60
    loss_history_list = []
    
    # Thiết lập hàm mất mát ban đầu mô phỏng giảm dần theo hàm mũ
    initial_loss_value = 1000.0

    def update_animation_frame(frame_index):
        # Tính toán tỷ lệ tiến độ (từ 0.0 đến 1.0)
        progress_ratio = frame_index / (total_animation_frames - 1)
        
        # Mô phỏng quá trình mạng nơ-ron học (từ nhiễu ngẫu nhiên tiến dần đến nghiệm thực tế)
        random_noise_tensor = (numpy.random.rand(spatial_resolution, spatial_resolution) - 0.5) * 2.0
        predicted_vector_potential = true_magnetic_vector_potential * progress_ratio + random_noise_tensor * (1.0 - progress_ratio)
        predicted_vector_potential = predicted_vector_potential * boundary_mask # Ép điều kiện biên

        # Mô phỏng sai số phương trình vật lý (PDE Residual giảm dần về 0)
        pde_residual_field = (true_magnetic_vector_potential - predicted_vector_potential) * 10.0
        
        # Ghi nhận hàm mất mát (Loss)
        current_loss_value = initial_loss_value * numpy.exp(-5.0 * progress_ratio) + numpy.random.rand() * 10.0 * (1.0 - progress_ratio)
        if frame_index == 0:
            loss_history_list.clear()
        loss_history_list.append(current_loss_value)

        # Xóa các đồ thị cũ để vẽ khung hình mới
        axes_array[0, 0].clear()
        axes_array[0, 1].clear()
        axes_array[1, 0].clear()
        axes_array[1, 1].clear()

        # -------------------------------------------------------------------
        # Đồ thị 1: Bước 1 - Lấy mẫu tọa độ (Collocation Sampling)
        # -------------------------------------------------------------------
        number_of_samples = 300
        sampled_x_coordinates = numpy.random.uniform(-2.0, 2.0, number_of_samples)
        sampled_y_coordinates = numpy.random.uniform(-2.0, 2.0, number_of_samples)
        
        axes_array[0, 0].scatter(sampled_x_coordinates, sampled_y_coordinates, color='black', s=5, alpha=0.6)
        axes_array[0, 0].set_title("1. Lấy Mẫu Tọa Độ & Nội Suy Vật Liệu")
        axes_array[0, 0].set_xlim(-2.0, 2.0)
        axes_array[0, 0].set_ylim(-2.0, 2.0)
        axes_array[0, 0].set_aspect('equal')

        # -------------------------------------------------------------------
        # Đồ thị 2: Bước 2 & 3 - Truyền xuôi & Đạo hàm (Dự đoán A_z)
        # -------------------------------------------------------------------
        contour_plot_prediction = axes_array[0, 1].contourf(
            x_mesh_grid, y_mesh_grid, predicted_vector_potential, 
            levels=40, cmap="jet", vmin=-1.0, vmax=1.0
        )
        axes_array[0, 1].set_title("2 & 3. Truyền Xuôi & Đạo Hàm Không Gian ($A_z$)")
        axes_array[0, 1].set_aspect('equal')

        # -------------------------------------------------------------------
        # Đồ thị 3: Bước 4 - Sai số phương trình vật lý (PDE Residual)
        # -------------------------------------------------------------------
        contour_plot_residual = axes_array[1, 0].contourf(
            x_mesh_grid, y_mesh_grid, numpy.abs(pde_residual_field), 
            levels=40, cmap="Reds", vmin=0.0, vmax=10.0
        )
        axes_array[1, 0].set_title("4. Sai Số Phương Trình PDE")
        axes_array[1, 0].set_aspect('equal')

        # -------------------------------------------------------------------
        # Đồ thị 4: Bước 5 - Cập nhật trọng số (Optimization Loss)
        # -------------------------------------------------------------------
        axes_array[1, 1].plot(range(len(loss_history_list)), loss_history_list, color='blue', linewidth=2.0)
        axes_array[1, 1].set_title("5. Tối Ưu Hóa Trọng Số (PDE Loss)")
        axes_array[1, 1].set_xlim(0, total_animation_frames)
        axes_array[1, 1].set_ylim(0, initial_loss_value)
        axes_array[1, 1].set_yscale('log')
        axes_array[1, 1].set_xlabel("Vòng Lặp (Epoch)")
        axes_array[1, 1].grid(True, alpha=0.3)
        
        matplotlib.pyplot.tight_layout()

    print("Đang tiến hành tạo ảnh động (GIF)... Vui lòng đợi.")
    
    animation_object = matplotlib.animation.FuncAnimation(
        figure_object, 
        update_animation_frame, 
        frames=total_animation_frames, 
        interval=100, # 100 mili-giây cho mỗi khung hình
        repeat_delay=2000
    )

    # Lưu thành tệp GIF sử dụng PillowWriter (không cần cài thêm thư viện ngoài)
    pillow_writer_object = matplotlib.animation.PillowWriter(fps=10)
    animation_object.save("pinn_training_process.gif", writer=pillow_writer_object)
    
    print("Đã xuất file thành công: pinn_training_process.gif")

if __name__ == "__main__":
    generate_pinn_training_animation()