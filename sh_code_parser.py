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