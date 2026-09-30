import os
import shutil
from pathlib import Path

def restructure_source_directory():
    current_file_path = Path(__file__).resolve()
    project_root = current_file_path.parent.parent
    source_directory = project_root / "src"

    if not source_directory.exists():
        return

    obsolete_folders = [
        "model", "physics", "script", "collocation_sampling", 
        "neural_networks", "physics_domain", "training_process",
        "training_manager", "physics_informed_model"
    ]
    
    for obsolete_folder in obsolete_folders:
        old_path = source_directory / obsolete_folder
        if old_path.exists():
            try:
                shutil.rmtree(str(old_path))
            except Exception:
                pass

    hierarchical_structure = {
        "training_manager": [
            "curriculum_training_manager.py"
        ],
        "training_manager/collocation_sampling": [
            "sobol_sequence_sampler.py",
            "geometry_adaptive_sampler.py"
        ],
        "physics_informed_model": [
            "trial_function_wrapper.py"
        ],
        "physics_informed_model/neural_networks": [
            "physics_neural_network.py"
        ],
        "physics_informed_model/geometry_engine": [
            "signed_distance_functions.py",
            "boolean_r_functions.py",
            "subdomain_material_mapping.py"
        ],
        "physics_informed_model/physics_domain/materials": [
            "material_permeability_properties.py",
            "b_h_curve_interpolator.py"
        ],
        "physics_informed_model/physics_domain/physical_equations": [
            "maxwell_partial_differential_equation_loss.py"
        ]
    }

    for folder_relative_path, files in hierarchical_structure.items():
        folder_path = source_directory / folder_relative_path
        folder_path.mkdir(parents=True, exist_ok=True)
        
        for file_name in files:
            file_path = folder_path / file_name
            with open(file_path, "w", encoding="utf-8") as file_object:
                file_object.write("")

if __name__ == "__main__":
    restructure_source_directory()