import os
import sys
# make project root (parent of 'backend') available on sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
if project_root not in sys.path:
    print(f"Adding {project_root} to sys.path")
    sys.path.insert(0, project_root)
else:
    print(f"{project_root} already in sys.path. Continuing...")
