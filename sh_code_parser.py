import re
import globals
import sh_code_main
import importlib

importlib.reload(globals)


class TreeNode:
    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right

    def __repr__(self):
        return f"TreeNode({self.value}, {self.left}, {self.right})"


def is_float(value):
    if value is None:
        return False
    # Regular expression to match a float number
    float_pattern = r'^[+-]?(\d+(\.\d*)?|\.\d+)$'
    return bool(re.match(float_pattern, value))
