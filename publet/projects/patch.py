def validate_ops(ops):
    if not ops:
        return False

    if not isinstance(ops, list):
        return False

    if not all(map(lambda x: 'op' in x, ops)):
        return False

    return True
