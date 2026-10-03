import torch

def evaluate_global_physical_properties(segments_list, points_tensor, vacuum_reluctivity, steepness=5000.0):
    number_of_points = points_tensor.shape[0]
    computation_device = points_tensor.device
    
    global_reluctivity_tensor = torch.full((number_of_points, 1), vacuum_reluctivity, dtype=torch.float32, device=computation_device)
    global_coercive_field_x_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)
    global_coercive_field_y_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)
    global_current_density_z_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)
    global_material_classification_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)

    sorted_segments = sorted(segments_list, key=lambda s: s.priority)
    material_index_counter = 1.0

    for segment_object in sorted_segments:
        signed_distance_field = segment_object.compute_signed_distance_field(points_tensor)
        
        mask_smooth = torch.sigmoid(-steepness * signed_distance_field).view(-1, 1)
        
        seg_reluctivity = segment_object.evaluate_reluctivity(points_tensor)
        hx_tensor, hy_tensor = segment_object.evaluate_magnetization_vector(points_tensor)
        seg_jz = segment_object.evaluate_current_density(points_tensor)
        
        inv_mask = 1.0 - mask_smooth
        global_reluctivity_tensor = global_reluctivity_tensor * inv_mask + seg_reluctivity * mask_smooth
        global_coercive_field_x_tensor = global_coercive_field_x_tensor * inv_mask + hx_tensor * mask_smooth
        global_coercive_field_y_tensor = global_coercive_field_y_tensor * inv_mask + hy_tensor * mask_smooth
        global_current_density_z_tensor = global_current_density_z_tensor * inv_mask + seg_jz * mask_smooth
        
        global_material_classification_tensor = global_material_classification_tensor * inv_mask + material_index_counter * mask_smooth
        
        material_index_counter += 1.0

    return {
        "reluctivity": global_reluctivity_tensor,
        "coercive_field_x": global_coercive_field_x_tensor,
        "coercive_field_y": global_coercive_field_y_tensor,
        "current_density_z": global_current_density_z_tensor,
        "material_classification": global_material_classification_tensor
    }
