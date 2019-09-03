

class menu(object):
    def __init__(self):
        pass

    def find(self, parent):
        sub = self.sub_menu
        for m in sub:
            if m.name == parent:
                return m
        return None

    def __setattr__(self, name, value):
        self.__dict__[name] = value

    @property
    def sub_menu(self):
        if not hasattr(self, '_sub'):
            setattr(self, '_sub', [])

        return self._sub
