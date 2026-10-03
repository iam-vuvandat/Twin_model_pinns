import os

def sharpen_material_boundary():
    base_directory = os.path.dirname(os.path.abspath(__file__))
    project_root_directory = os.path.abspath(os.path.join(base_directory, '..'))
    
    geometry_file_path = os.path.join(project_root_directory, 'geometry_engine', 'geometry.py')

    # Cập nhật steepness lên 2000.0 (hoặc bạn có thể tự tinh chỉnh con số này)
    geometry_source_code = """import torch
from geometry_engine.segment.segment import Segment
from geometry_engine.global_signed_distance_field import compute_global_signed_distance_field
from geometry_engine.global_physical_properties_evaluation import evaluate_global_physical_properties
from geometry_engine.geometry_visualizer import plot_geometry_problem

class Geometry:
    # [CẬP NHẬT]: Tăng độ dốc (steepness) lên 2000.0 để biên dạng vật liệu sắc nét và dốc hơn
    def __init__(self, steepness=2000.0):
        self.segments_list = []
        self.vacuum_reluctivity = 795774.715459
        self.steepness = steepness

    def add_segment(self, segment_object):
        self.segments_list.append(segment_object)
        return self

    def compute_global_signed_distance_field(self, points_tensor):
        return compute_global_signed_distance_field(self.segments_list, points_tensor)

    def evaluate_global_physical_properties(self, points_tensor):
        return evaluate_global_physical_properties(self.segments_list, points_tensor, self.vacuum_reluctivity, self.steepness)

    def plot_problem_definition(self, x_boundaries_tuple, y_boundaries_tuple, resolution=100):
        plot_geometry_problem(self, x_boundaries_tuple, y_boundaries_tuple, resolution)
"""

    with open(geometry_file_path, 'w', encoding='utf-8') as f:
        f.write(geometry_source_code)
        
    print("Đã tăng độ dốc (steepness) ranh giới vật liệu thành công!")

if __name__ == '__main__':
    sharpen_material_boundary()