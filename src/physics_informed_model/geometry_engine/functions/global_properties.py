import torch

def evaluate_global_physical_properties(segments_list, points_tensor, vacuum_reluctivity):
    number_of_points = points_tensor.shape[0]
    computation_device = points_tensor.device
    
    global_relative_permeability_tensor = torch.ones((number_of_points, 1), dtype=torch.float32, device=computation_device)
    global_coercive_field_x_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)
    global_coercive_field_y_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)
    global_current_density_z_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)
    global_material_classification_tensor = torch.zeros((number_of_points, 1), dtype=torch.float32, device=computation_device)

    material_index_counter = 1.0

    for segment_object in segments_list:
        signed_distance_field = segment_object.compute_signed_distance_field(points_tensor)
        mask_tensor = signed_distance_field <= 0.0
        
        if mask_tensor.any():
            global_relative_permeability_tensor[mask_tensor] = segment_object.relative_permeability
            global_current_density_z_tensor[mask_tensor] = segment_object.current_density_z_axis
            global_coercive_field_x_tensor[mask_tensor] = segment_object.coercive_field_magnitude
            global_material_classification_tensor[mask_tensor] = material_index_counter
        
        material_index_counter += 1.0

    global_reluctivity_tensor = vacuum_reluctivity / global_relative_permeability_tensor

    return {
        "reluctivity": global_reluctivity_tensor,
        "relative_permeability": global_relative_permeability_tensor,
        "coercive_field_x": global_coercive_field_x_tensor,
        "coercive_field_y": global_coercive_field_y_tensor,
        "current_density_z": global_current_density_z_tensor,
        "material_classification": global_material_classification_tensor
    }
