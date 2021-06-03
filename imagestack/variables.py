from . import *
import warnings


class VariableInterface:
    @staticmethod
    def get_variable(variable):
        if issubclass(type(variable), VariableInterface):
            return variable.get()
        if isinstance(variable, list) or isinstance(variable, tuple):
            return [VariableInterface.get_variable(v) for v in variable]
        return variable

    @staticmethod
    def one_key_to_var(key, value):
        if key is None:
            return value
        if issubclass(type(key), VariableInterface):
            key.set(value)
            return key.get()
        if isinstance(key, str) and hasattr(value, key):
            return getattr(value, key)
        return value[key]

    @staticmethod
    def key_to_var(key, value):
        if isinstance(key, list) or isinstance(key, tuple):
            v = value
            for k in key:
                v = VariableInterface.one_key_to_var(k, v)
            return v
        return VariableInterface.one_key_to_var(key, value)

    def set(self, value_dict):
        raise Exception('Raw Usage of VariableInterface forbidden')

    def get(self):
        raise Exception('Raw Usage of VariableInterface forbidden')


class Variable(VariableInterface):
    def __init__(self, key=None):
        self.key = key
        self.value = None
        self.operations = []
        self.after_operations = []

    def add_operation(self, op_name, args, kwargs):
        self.operations.append((op_name, (args, kwargs)))

    def add_after_operation(self, op):
        self.after_operations.append(op)

    def set(self, value):
        self.set_value(self.key_to_var(self.key, value))

    def set_value(self, value):
        self.value = value
        for op in self.operations:
            self.value = getattr(self.value, op[0])(*op[1][0], **op[1][1])

    def get(self):
        v = self.get_variable(self.value)
        for op in self.after_operations:
            v = op(v)
        return v

    def formatted(self, s):
        self.add_after_operation(lambda x: s.format(x))
        return self

    # TO-DO: implement all necessary requests

    def __add__(self, *args, **kwargs):
        self.add_operation('__add__', args, kwargs)
        return self

    def __mul__(self, *args, **kwargs):
        self.add_operation('__mul__', args, kwargs)
        return self

    def __sub__(self, *args, **kwargs):
        self.add_operation('__sub__', args, kwargs)
        return self

    def __truediv__(self, *args, **kwargs):
        self.add_operation('__truediv__', args, kwargs)
        return self

    def __floordiv__(self, *args, **kwargs):
        self.add_operation('__floordiv__', args, kwargs)
        return self

    def __getitem__(self, *args, **kwargs):
        self.add_operation('__getitem__', args, kwargs)
        return self


class EqualityVariable(Variable):
    def __init__(self, key, compare, on_equals, on_greater, on_smaller=None):
        super().__init__(key)
        self.compare = compare
        self.on_equals = on_equals
        self.on_greater = on_greater
        self.on_smaller = on_smaller

    def set(self, value):
        super().set(value)
        for v in [self.on_equals, self.on_greater, self.on_smaller]:
            if issubclass(type(v), VariableInterface):
                v.set(value)

    def get(self):
        if self.value == self.compare:
            return VariableInterface.get_variable(self.on_equals)
        if self.on_smaller is None or self.value > self.compare:
            return VariableInterface.get_variable(self.on_greater)
        return VariableInterface.get_variable(self.on_smaller)


class LengthVariable(Variable):
    def set(self, value):
        super().set_value(len(self.key_to_var(self.key, value)))

    def get(self):
        return super().get()


class IteratorVariable(Variable):
    current_i = 0
    max_i = 0
    iterable = None
    after_key = None

    def set(self, value):
        self.iterable = self.key_to_var(self.key, value)
        self.max_i = len(self.iterable)

    def get(self):
        if self.current_i < self.max_i:
            self.set_value(self.key_to_var(self.after_key, self.iterable[self.current_i]))
            self.current_i += 1
        return super().get()

    def __call__(self, key=None):
        self.after_key = key
        return self


class SingleColorVariable(Variable):
    def __init__(self, key):
        super().__init__(key)
        self.operations = []

    def set(self, value):
        super().set_value(SingleColor(self.key_to_var(self.key, value)))

    def lightened(self, *args, **kwargs):
        self.add_operation('lightened', args, kwargs)
        return self

    def darkened(self, *args, **kwargs):
        self.add_operation('darkened', args, kwargs)
        return self

    def alpha(self, *args, **kwargs):
        self.add_operation('alpha', args, kwargs)
        return self


class FormattedVariables(VariableInterface):
    def __init__(self, keys, vformat):
        self.vars = [Variable(key) for key in keys]
        self.vformat = vformat

    def set(self, value):
        for var in self.vars:
            var.set(value)

    def get(self):
        return self.vformat.format(*[v.get() for v in self.vars])


class VariableKwargManager:
    def used_kwarg(self, key):
        self.used_kwargs.append(key)

    def get_kwarg(self, key, default=None):
        if default is not None and key not in self.kwargs:
            return default
        if key not in self.kwargs:
            raise Exception('"{}" was not found in {}'.format(key, type(self).__name__))
        self.used_kwargs.append(key)
        value = self.kwargs[key]
        return VariableInterface.get_variable(value)

    def get_raw_kwarg(self, key):
        if key not in self.kwargs:
            raise Exception('"{}" was not found in {}'.format(key, type(self).__name__))
        self.used_kwargs.append(key)
        return self.kwargs[key]

    def set_kwarg(self, key, value):
        self.kwargs[key] = value

    def __init__(self, **kwargs):
        self.used_kwargs = []
        self.kwargs = kwargs

    def _init_finished(self):
        if 'no-check' in self.kwargs and self.kwargs['no-check'] is True:
            return
        for key in self.kwargs.keys():
            if key not in self.used_kwargs:
                warnings.warn('{} "{}" was not used'.format(type(self).__name__, key))
