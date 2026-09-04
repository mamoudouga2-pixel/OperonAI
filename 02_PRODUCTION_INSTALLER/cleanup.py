import shutil

def remove_tree(path):
    if path.exists(): shutil.rmtree(path)
