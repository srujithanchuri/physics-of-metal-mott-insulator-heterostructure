import os
import shutil

def stage_dir(src, dest):
    if os.path.exists(dest):
        shutil.rmtree(dest)
    os.makedirs(dest)
    for root, dirs, files in os.walk(src):
        # EXCLUDE JUNK FOLDERS
        dirs[:] = [d for d in dirs if d not in [".venv", "build", "dist", ".idea", "results", "__pycache__", "data"]]
        for file in files:
            if file.endswith(".py") or file.endswith(".bat"):
                src_file = os.path.join(root, file)
                rel_path = os.path.relpath(root, src)
                dest_dir = os.path.join(dest, rel_path)
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)
                shutil.copy2(src_file, os.path.join(dest_dir, file))

print("Staging clean self_energy...")
stage_dir("../self_energy", "staging/self_energy")
print("Staging clean susceptibility...")
stage_dir("../susceptibility", "staging/susceptibility")

print("Staging master_app...")
shutil.copy2("master_app.py", "staging/master_app.py")
shutil.copy2("master_app_cpu.py", "staging/master_app_cpu.py")

