def ensure(paths):
    for p in paths.all_dirs(): p.mkdir(parents=True,exist_ok=True)
