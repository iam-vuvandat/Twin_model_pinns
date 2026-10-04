import os

def execute_step_1():
    # Xác định đường dẫn thư mục gốc
    base_directory = os.path.dirname(os.path.abspath(__file__))
    project_root_directory = os.path.abspath(os.path.join(base_directory, '..'))
    
    # Đường dẫn tới tệp cần sửa ở Bước 1
    target_file_path = os.path.join(
        project_root_directory, 
        'geometry_engine', 
        'global_physical_properties_evaluation.py'
    )
    
    # Nội dung mới của tệp global_physical_properties_evaluation.py
    new_code = """import torch

def evaluate_global_physical_properties(segments_list, points_tensor, vacuum_reluctivity, steepness=5000.0):
    number_of_points = points_tensor.shape[0]
    computation_device = points_tensor.device
    
    global_reluctivity_tensor = torch.full((number_of_points, 1), vacuum_reluctivity, dtype=torch.float32, device=computation_device)
    global_coercive_field_x_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)
    global_coercive_field_y_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)
    global_current_density_z_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)
    global_material_classification_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)

    material_index_counter = 1.0
    
    # BƯỚC 1: Khởi tạo từ điển lưu trữ mặt nạ (masks_dict)
    masks_dict = {}

    for segment_object in segments_list:
        signed_distance_field = segment_object.compute_signed_distance_field(points_tensor)
        
        mask_smooth = torch.sigmoid(-steepness * signed_distance_field).view(-1, 1)
        
        # Lưu mặt nạ vào từ điển theo tên vật liệu
        # Nếu có nhiều vật thể cùng loại (VD: 2 khối nam châm), ta cộng dồn mặt nạ của chúng lại
        mat_name = segment_object.material_name
        if mat_name in masks_dict:
            masks_dict[mat_name] = masks_dict[mat_name] + mask_smooth
        else:
            masks_dict[mat_name] = mask_smooth
        
        seg_reluctivity = segment_object.evaluate_reluctivity(points_tensor)
        hx_tensor, hy_tensor = segment_object.evaluate_magnetization_vector(points_tensor)
        seg_jz = segment_object.evaluate_current_density(points_tensor)
        
        global_reluctivity_tensor = global_reluctivity_tensor + mask_smooth * (seg_reluctivity - vacuum_reluctivity)
        global_coercive_field_x_tensor = global_coercive_field_x_tensor + mask_smooth * hx_tensor
        global_coercive_field_y_tensor = global_coercive_field_y_tensor + mask_smooth * hy_tensor
        global_current_density_z_tensor = global_current_density_z_tensor + mask_smooth * seg_jz
        
        global_material_classification_tensor = global_material_classification_tensor + mask_smooth * material_index_counter
        
        material_index_counter += 1.0

    # Kẹp (clamp) các giá trị mặt nạ trong khoảng [0, 1] để tránh vượt ngưỡng tại các vùng giao nhau
    for key in masks_dict:
        masks_dict[key] = torch.clamp(masks_dict[key], min=0.0, max=1.0)

    # Trả về thêm masks_dict để phân luồng cho mạng nơ-ron chuyên gia
    return {
        "reluctivity": global_reluctivity_tensor,
        "coercive_field_x": global_coercive_field_x_tensor,
        "coercive_field_y": global_coercive_field_y_tensor,
        "current_density_z": global_current_density_z_tensor,
        "material_classification": global_material_classification_tensor,
        "masks_dict": masks_dict
    }
"""
    
    # Ghi đè file
    with open(target_file_path, 'w', encoding='utf-8') as f:
        f.write(new_code)
        
    print(f"BƯỚC 1 HOÀN TẤT: Đã cập nhật thành công tệp:\n{target_file_path}")
    print("Hàm evaluate_global_physical_properties hiện đã trích xuất và trả về masks_dict.")

if __name__ == "__main__":
    execute_step_1()