class Settings:
    class __Settings:

        def __init__(self):
            None

    instance = None
    def __init__(self):
        if not Settings.instance:
            Settings.instance = Settings.__Settings()

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __setattr__(self, name, value):
        return setattr(self.instance, name, value)
