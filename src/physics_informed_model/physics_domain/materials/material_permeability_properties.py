import torch

class MaterialMapping:
    def __init__(self, nu_0=795774.715459, mu_r_iron=1000.0, mu_r_magnet=1.05):
        self.nu_0 = nu_0
        self.nu_iron = nu_0 / mu_r_iron
        self.nu_magnet = nu_0 / mu_r_magnet

    def get_reluctivity(self, iron_mask, magnet_mask):
        # 4. SỬA LỖI GIAO NHAU MẶT NẠ: Kẹp giá trị air_mask tránh số âm
        overlap_mask = iron_mask + magnet_mask
        air_mask = torch.clamp(1.0 - overlap_mask, min=0.0, max=1.0)
        
        nu_out = iron_mask * self.nu_iron + magnet_mask * self.nu_magnet + air_mask * self.nu_0
        return nu_out

    def get_current_density(self, points, slot_masks_dict, slot_current_dict):
        device = points.device
        dtype = points.dtype
        J_z = torch.zeros((points.shape[0], 1), device=device, dtype=dtype)
        
        for slot_name, mask in slot_masks_dict.items():
            if slot_name in slot_current_dict:
                current_value = slot_current_dict[slot_name]
                J_z += mask * current_value
                
        return J_z
