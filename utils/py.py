# Tệp tin: utils/refactor_source_directory.py
import os
import shutil
from pathlib import Path

def restructure_source_directory():
    current_file_path = Path(__file__).resolve()
    project_root = current_file_path.parent.parent
    source_directory = project_root / "src"

    if not source_directory.exists():
        print(f"Lỗi: Không tìm thấy thư mục {source_directory}.")
        print("Vui lòng đảm bảo tệp tin này được đặt đúng bên trong thư mục 'utils/'.")
        return

    print(f"Đang tiến hành dọn dẹp và tái cấu trúc thư mục: {source_directory}")

    # Danh sách các thư mục cũ cần xóa bỏ hoàn toàn (ngoại trừ thư mục ansys)
    obsolete_folders = ["model", "physics", "script"]
    
    print("\n[Bước 1/2] Đang xóa bỏ vĩnh viễn các thư mục cũ...")
    for obsolete_folder in obsolete_folders:
        old_path = source_directory / obsolete_folder
        if old_path.exists():
            try:
                shutil.rmtree(str(old_path))
                print(f"  -> Đã xóa vĩnh viễn thư mục cũ: '{obsolete_folder}'.")
            except Exception as error:
                print(f"  -> Lỗi khi xóa thư mục '{obsolete_folder}': {error}")

    # Định nghĩa cấu trúc mới với tên gọi đầy đủ, rõ nghĩa, không viết tắt
    new_project_structure = {
        "collocation_sampling": [
            "sobol_sequence_sampler.py",
        ],
        "neural_networks": [
            "geometry_neural_network.py",
            "physics_neural_network.py",
            "parallel_neural_networks_wrapper.py"
        ],
        "physics_domain": [
            "material_permeability_properties.py",
            "magnetization_excitation_source.py",
            "maxwell_partial_differential_equation_loss.py"
        ],
        "training_process": [
            "curriculum_training_manager.py"
        ]
    }

    print("\n[Bước 2/2] Đang tự động tạo mới các thư mục và tệp tin trống...")
    for folder_name, files in new_project_structure.items():
        folder_path = source_directory / folder_name
        folder_path.mkdir(parents=True, exist_ok=True)
        print(f"[Tạo thư mục] {folder_name}")
        
        for file_name in files:
            file_path = folder_path / file_name
            with open(file_path, "w", encoding="utf-8") as file_object:
                file_object.write(f'"""\nModule: {file_name}\nMô tả cấu trúc cho khối {folder_name}.\n"""\n')
            print(f"  + [Tạo tệp tin] {file_name}")

    print("\nHoàn tất quá trình tái cấu trúc mã nguồn!")
    print("Thư mục 'ansys_electronic_desktop' được bảo toàn nguyên vẹn.")

if __name__ == "__main__":
    restructure_source_directory()