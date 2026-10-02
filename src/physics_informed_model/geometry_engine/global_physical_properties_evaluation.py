import torch

def evaluate_global_physical_properties(segments_list, points_tensor, vacuum_reluctivity):
    number_of_points = points_tensor.shape[0]
    computation_device = points_tensor.device
    
    global_reluctivity_tensor = torch.full((number_of_points, 1), vacuum_reluctivity, dtype=torch.float32, device=computation_device)
    global_coercive_field_x_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)
    global_coercive_field_y_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)
    global_current_density_z_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)
    global_material_classification_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)

    material_index_counter = 1.0

    for segment_object in segments_list:
        signed_distance_field = segment_object.compute_signed_distance_field(points_tensor)
        mask_tensor = signed_distance_field <= 0.0
        mask_1d = mask_tensor.squeeze()
        
        if mask_1d.any():
            points_in_segment = points_tensor[mask_1d]
            
            global_reluctivity_tensor[mask_1d] = segment_object.evaluate_reluctivity(points_in_segment)
            
            hx_tensor, hy_tensor = segment_object.evaluate_magnetization_vector(points_in_segment)
            global_coercive_field_x_tensor[mask_1d] = hx_tensor
            global_coercive_field_y_tensor[mask_1d] = hy_tensor
            
            global_current_density_z_tensor[mask_1d] = segment_object.evaluate_current_density(points_in_segment)
            
            global_material_classification_tensor[mask_1d] = material_index_counter
        
        material_index_counter += 1.0

    return {
        "reluctivity": global_reluctivity_tensor,
        "coercive_field_x": global_coercive_field_x_tensor,
        "coercive_field_y": global_coercive_field_y_tensor,
        "current_density_z": global_current_density_z_tensor,
        "material_classification": global_material_classification_tensor
    }
