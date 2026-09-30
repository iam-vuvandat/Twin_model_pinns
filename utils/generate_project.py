import os
import shutil

def reorganize_project():
    base_dir = os.getcwd()
    
    examples_dir = os.path.join(base_dir, 'examples')
    os.makedirs(examples_dir, exist_ok=True)
    
    for demo_file in ['demo.py', 'demo2.py', 'demo3.py']:
        src = os.path.join(base_dir, demo_file)
        if os.path.exists(src):
            shutil.move(src, os.path.join(examples_dir, demo_file))
            
    ansys_old = os.path.join(base_dir, 'src', 'ansys_electronic_desktop', 'rmxprt', 'synchronous_machine', 'reluctance_synchronous_machine')
    ansys_new = os.path.join(base_dir, 'src', 'ansys_aedt')
    os.makedirs(ansys_new, exist_ok=True)
    
    if os.path.exists(ansys_old):
        config_old = os.path.join(ansys_old, 'configuation.py')
        if os.path.exists(config_old):
            shutil.move(config_old, os.path.join(ansys_new, 'configuration.py'))
            
        for f in ['reluctance_synchronous_motor.py']:
            src = os.path.join(ansys_old, f)
            if os.path.exists(src):
                shutil.move(src, os.path.join(ansys_new, f))
                
        utils_old = os.path.join(ansys_old, 'utils')
        if os.path.exists(utils_old):
            for f in ['create_model.py', 'reset_ansys_environment.py']:
                src = os.path.join(utils_old, f)
                if os.path.exists(src):
                    shutil.move(src, os.path.join(ansys_new, f))
                    
    pinn_dir = os.path.join(base_dir, 'src', 'physics_informed_model')
    
    nn_dir = os.path.join(pinn_dir, 'neural_networks')
    if os.path.exists(nn_dir):
        for f in ['pinn_architecture.py', 'training_manager.py', 'physics_neural_network.py']:
            src = os.path.join(nn_dir, f)
            if os.path.exists(src):
                shutil.move(src, os.path.join(pinn_dir, f))
                
    tm_old_dir = os.path.join(base_dir, 'src', 'training_manager')
    if os.path.exists(tm_old_dir):
        col_old = os.path.join(tm_old_dir, 'collocation_sampling', 'collocation_sampling.py')
        col_new_dir = os.path.join(pinn_dir, 'physics_domain')
        os.makedirs(col_new_dir, exist_ok=True)
        if os.path.exists(col_old):
            shutil.move(col_old, os.path.join(col_new_dir, 'collocation_sampling.py'))
            
        curriculum_old = os.path.join(tm_old_dir, 'curriculum_training_manager.py')
        if os.path.exists(curriculum_old):
            shutil.move(curriculum_old, os.path.join(pinn_dir, 'curriculum_training_manager.py'))

    dirs_to_remove = [
        os.path.join(base_dir, 'src', 'ansys_electronic_desktop'),
        os.path.join(base_dir, 'src', 'training_manager'),
        os.path.join(pinn_dir, 'neural_networks')
    ]
    
    for d in dirs_to_remove:
        if os.path.exists(d):
            shutil.rmtree(d, ignore_errors=True)

if __name__ == "__main__":
    reorganize_project()