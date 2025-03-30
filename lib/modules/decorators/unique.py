def unique(cls):
    is_created = False
    def get_instance(*args, **kwargs):
        nonlocal is_created
        if is_created:
            raise NotImplementedError('%s is a unique object' % cls.__name__)
        is_created = True
        return cls(*args, **kwargs)
    get_instance.__dict__.update(cls.__dict__)
    return get_instance