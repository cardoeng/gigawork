from click import ParamType

class GitReference(ParamType):
    name = "ref"

    # We could also check if the reference is valid.
    # This is done by GitPython later though.
    # def convert(self, value, param, ctx):
            