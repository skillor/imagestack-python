from . import *
import copy
import ast


class ImageStackResolve:
    def __init__(self, creatable):
        self.untouched_creatable = creatable
        self.current_arg = None

    def _resolve_list(self, x):
        for value in x:
            self._resolve(value)

    def _resolve_dict(self, d):
        for key, value in d.items():
            self._resolve(value)

    def _resolve(self, i):
        if isinstance(i, list) or isinstance(i, tuple):
            self._resolve_list(i)
        elif isinstance(i, dict):
            self._resolve_dict(i)
        elif issubclass(type(i), VariableKwargManager):
            self._resolve_dict(i.kwargs)
        elif isinstance(i, LinearGradientColor):
            self._resolve(i.color1)
            self._resolve(i.color2)
        elif issubclass(type(i), VariableInterface):
            i.set(self.current_arg)

    def _resolve_variables(self):
        self._resolve(self.creatable)

    def _resolve_init(self):
        self.creatable._init()

    def __call__(self, arg=None):
        self.current_arg = arg
        self.creatable = copy.deepcopy(self.untouched_creatable)
        self.to_init = []
        self._resolve_variables()
        self._resolve_init()
        self.current_arg = None
        return self.creatable


class IType:
    def __init__(self, index, name):
        self.index = index
        self.name = name

    def __str__(self):
        return self.name


class Node:
    CALL = IType(0, 'Call')
    KEYWORD = IType(1, 'Keyword')
    LIST = IType(2, 'List')
    TUPLE = IType(3, 'Tuple')
    CONSTANT = IType(4, 'Constant')
    UNARY_OP = IType(5, 'UnaryOp')
    BIN_OP = IType(6, 'BinOp')
    ATTRIBUTE = IType(7, 'Attribute')

    def __init__(self, value, itype, parent):
        self.type = itype
        self.value = value
        self.parent = parent
        self.children = []

    def add_child(self, value, itype):
        node = Node(value=value, itype=itype, parent=self)
        self.children.append(node)
        return node

    def last_child(self):
        if len(self.children) == 0:
            return None
        return self.children[-1]

    def base(self):
        base = self
        while base.parent is not None:
            base = base.parent
        return base

    def __str__(self, level=0):
        ret = "\t" * level + str(self.type) + ' | ' + str(self.value) \
              + "\n"
        for child in self.children:
            ret += child.__str__(level + 1)
        return ret


class ImageStackAnalyser(ast.NodeVisitor):
    def __init__(self):
        self.tree = None

    def incremental_visit(self, node, value, itype):
        if self.tree is None:
            self.tree = Node(value=value, itype=itype, parent=None)
            self.generic_visit(node)
        else:
            last = self.tree
            self.tree = self.tree.add_child(value=value, itype=itype)
            self.generic_visit(node)
            self.tree = last

    def visit_Call(self, node):
        self.incremental_visit(node, value=None, itype=Node.CALL)

    def visit_keyword(self, node):
        self.incremental_visit(node, value=node.arg, itype=Node.KEYWORD)

    def visit_List(self, node):
        self.incremental_visit(node, value=None, itype=Node.LIST)

    def visit_Tuple(self, node):
        self.incremental_visit(node, value=None, itype=Node.TUPLE)

    def visit_Constant(self, node):
        self.incremental_visit(node, value=node.value, itype=Node.CONSTANT)

    def visit_UnaryOp(self, node):
        self.incremental_visit(node, value=type(node.op).__name__, itype=Node.UNARY_OP)

    def visit_BinOp(self, node):
        self.incremental_visit(node, value=type(node.op).__name__, itype=Node.BIN_OP)

    def visit_Attribute(self, node):
        self.incremental_visit(node, value=node.attr, itype=Node.ATTRIBUTE)

    def visit_Name(self, node):
        self.tree.value = node.id


class ImageStackParseVisitor:
    def __init__(self):
        self.image_stack = None

    def check_length(self, value):
        if isinstance(value, str) and len(value) > 500:
            raise Exception('Strings longer than 500 are not supported')
        if isinstance(value, (int, float)) and value > 10000:
            raise Exception('Values bigger than 10000 are not supported')

    def visit_call(self, node):
        args = []
        kwargs = {}

        if node.value is None:
            if len(node.children) < 1 or node.children[0].type not in [Node.ATTRIBUTE, Node.CALL]:
                raise Exception('These calls are pretty deep')

            cls = self.visit(node.children[0])
            children = node.children[1:]

        else:
            cls = ImageStackStringParser.ACCEPTED_CLASSES[node.value]
            children = node.children

        for child in children:
            if child.type == Node.KEYWORD:
                if len(child.children) != 1:
                    raise Exception('Keyword does not have exactly one child')
                kwargs[child.value] = self.visit(child.last_child())

            else:
                args.append(self.visit(child))

        return cls(*args, **kwargs)

    def visit_attribute(self, node):
        if len(node.children) != 1:
            raise Exception('Attribute does not have exactly one child')
        obj = self.visit(node.last_child())
        if type(obj) not in ImageStackStringParser.ACCEPTED_CLASSES.values():
            raise Exception('Attribute access not allowed for this class')
        if node.value[0] == '_':
            raise Exception('Access to protected attributes forbidden')
        return getattr(obj, node.value)

    def visit_list(self, node):
        li = []
        for child in node.children:
            li.append(self.visit(child))
        return li

    def visit_tuple(self, node):
        return tuple(self.visit_list(node))

    def visit_unary_op(self, node):
        if len(node.children) != 1:
            raise Exception('Unary Operator does not have exactly one child')
        if node.value == 'USub':
            return -self.visit(node.last_child())
        raise Exception('Unknown Unary Operator')

    def visit_bin_op(self, node):
        if len(node.children) != 2:
            raise Exception('Bin Operator does not have exactly two children')
        op1, op2 = node.children
        res = None
        if node.value == 'Add':
            res = self.visit(op1) + self.visit(op2)
        elif node.value == 'Sub':
            res = self.visit(op1) - self.visit(op2)
        elif node.value == 'Mult':
            res = self.visit(op1) * self.visit(op2)
        if res is not None:
            self.check_length(res)
            return res
        raise Exception('Unknown Bin Operator: {}'.format(node.value))

    def visit_constant(self, node):
        if len(node.children) != 0:
            raise Exception('Constant has a child')
        self.check_length(node.value)
        return node.value

    def visit(self, node):
        if node.type == Node.CALL:
            return self.visit_call(node)
        elif node.type == Node.ATTRIBUTE:
            return self.visit_attribute(node)
        elif node.type == Node.LIST:
            return self.visit_list(node)
        elif node.type == Node.TUPLE:
            return self.visit_tuple(node)
        elif node.type == Node.UNARY_OP:
            return self.visit_unary_op(node)
        elif node.type == Node.BIN_OP:
            return self.visit_bin_op(node)
        elif node.type == Node.CONSTANT:
            return self.visit_constant(node)

        raise Exception('Unhandled node in the tree {}'.format(node.type))


class ImageStackStringParser:
    ACCEPTED_CLASSES = {
        'ImageStack': ImageStack,
        'AnimatedImageStack': AnimatedImageStack,

        'EmptyLayer': EmptyLayer,
        'ColorLayer': ColorLayer,
        'RectangleLayer': RectangleLayer,
        'LineLayer': LineLayer,
        'TextLayer': TextLayer,
        'WebImageLayer': WebImageLayer,
        'EmojiLayer': EmojiLayer,
        'ProgressLayer': ProgressLayer,
        'PieLayer': PieLayer,
        'ListLayer': ListLayer,

        'SingleColor': SingleColor,
        'LinearGradientColor': LinearGradientColor,

        'RotationLayer': RotationLayer,

        'Variable': Variable,
        'SingleColorVariable': SingleColorVariable,
        'FormattedVariables': FormattedVariables,
        'EqualityVariable': EqualityVariable,
        'IteratorVariable': IteratorVariable,
        'LengthVariable': LengthVariable,
    }

    def __init__(self, string):
        tree = ast.parse(string)
        analyzer = ImageStackAnalyser()
        analyzer.visit(tree)
        self.node_tree = analyzer.tree

    def build(self):
        v = ImageStackParseVisitor()
        return v.visit(self.node_tree)


class ImageStackResolveString(ImageStackResolve):
    def __init__(self, string):
        self.string = string
        self.string_parser = ImageStackStringParser(self.string)
        super().__init__(self.string_parser.build())

    def __str__(self):
        return self.string
