def select_model(selection,available):
    if not selection:return None
    if isinstance(selection,str): selection={"model_id":selection}
    for item in available:
        if item.get("model_id")==selection.get("model_id"): return item
    return None
