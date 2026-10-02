import os
import sys

# Thêm thư mục hiện tại vào đường dẫn hệ thống để import các module nội bộ
current_directory = os.path.dirname(os.path.abspath(__file__))
if current_directory not in sys.path:
    sys.path.insert(0, current_directory)

import torch
from geometry_engine.geometry import Geometry
from geometry_engine.segment.segment import Segment
from physics_domain.collocation_sampler import CollocationSampler
from electro_magnetic_pinn import ElectroMagneticPINN

def main():
    # 1. Khởi tạo Hình học
    geometry_instance = Geometry()
    
    # 2. Định nghĩa lõi sắt và thêm vào Hình học
    core_vertices = [
        [-0.02, -0.02],
        [0.02, -0.02],
        [0.02, 0.02],
        [-0.02, 0.02]
    ]
    iron_segment = Segment(core_vertices).set_material_properties(
        name="iron_core",
        relative_permeability=1000.0,
        current_density_z_axis=0.0
    )
    geometry_instance.add_segment(iron_segment)
    
    # 3. Khởi tạo bộ lấy mẫu điểm trong không gian vật lý
    collocation_sampler_instance = CollocationSampler(
        x_boundaries_tuple=(-0.05, 0.05),
        y_boundaries_tuple=(-0.05, 0.05)
    )
    
    # 4. Khởi tạo mô hình PINN điện từ
    model = ElectroMagneticPINN(
        geometry_engine_instance=geometry_instance,
        collocation_sampler_instance=collocation_sampler_instance
    )
    
    # 5. Tiến hành huấn luyện mô hình (Curriculum Training)
    print("Bắt đầu quá trình huấn luyện mô hình...")
    model.execute_training_process(
        number_of_uniform_points=200,
        number_of_interface_points=50,
        distance_threshold=0.005,
        stages=2,
        epochs_per_stage=5
    )
    
    # 6. Kiểm thử: Lấy mẫu 10 điểm ngẫu nhiên mới và dự đoán Thế véc-tơ từ
    print("\nQuá trình huấn luyện hoàn tất. Bắt đầu dự đoán thử...")
    test_points = collocation_sampler_instance.generate_uniform_points_tensor(10)
    predictions = model.predict_magnetic_vector_potential(test_points)
    
    print("\nTọa độ điểm thử nghiệm (x, y):")
    print(test_points)
    print("\nThế véc-tơ từ dự đoán (Predicted A_z):")
    print(predictions)

# Điểm neo khởi chạy: Đảm bảo hàm main() sẽ được thực thi khi kịch bản chạy trực tiếp
if __name__ == "__main__":
    main()