class Debug:
    class __Debug:

        def __init__(self):
            self.print_optimized = False
            self.last_program = None

        def print_program(self):
            print("Current program:\n",self.last_program)

    instance = None
    def __init__(self):
        if not Debug.instance:
            Debug.instance = Debug.__Debug()

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __setattr__(self, name, value):
        return setattr(self.instance, name, value)
