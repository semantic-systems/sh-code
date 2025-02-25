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


def parse_expression(expression):
    expression = expression.strip()

    func_match = re.match(r"(TextQA|KGQA1|KGQA2)\((.+?)\)", expression)
    if func_match:
        func_name, func_arg = func_match.groups()
        return TreeNode(func_name, TreeNode(func_arg.strip()))

    if expression.startswith("JOIN("):
        start_index = len("JOIN(")
        inner_expr = expression[start_index:-1]
        left_expr, right_expr = split_expressions(inner_expr)
        return TreeNode("JOIN", parse_expression(left_expr), parse_expression(right_expr))

    elif expression.startswith("COMP_>") or expression.startswith("COMP_<") or expression.startswith("COMP_="):
        operator_type = expression[:6]
        start_index = len("COMP_>(")
        inner_expr = expression[start_index:-1]
        left_expr, right_expr = split_expressions(inner_expr)
        return TreeNode(operator_type, parse_expression(left_expr), parse_expression(right_expr))

    elif expression.startswith("AND("):
        start_index = len("AND(")
        inner_expr = expression[start_index:-1]
        left_expr, right_expr = split_expressions(inner_expr)
        return TreeNode("AND", parse_expression(left_expr), parse_expression(right_expr))

    elif expression.startswith("UNION("):
        start_index = len("UNION(")
        inner_expr = expression[start_index:-1]
        left_expr, right_expr = split_expressions(inner_expr)
        return TreeNode("UNION", parse_expression(left_expr), parse_expression(right_expr))

    else:
        return TreeNode(expression)


def split_expressions(inner_expr):
    # Helper function to split inner expressions at the top level
    # Handles nested expressions by counting parentheses
    depth = 0
    split_index = 0
    for i, char in enumerate(inner_expr):
        if char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
        elif char == ',' and depth == 0:
            split_index = i
            break
    left_expr = inner_expr[:split_index].strip()
    right_expr = inner_expr[split_index + 1:].strip()
    return left_expr, right_expr


def evaluate_with_tracking(node, current_uri=None):
    if node.value.startswith("COMP_"):
        left_value, left_entity = evaluate_subexpression_with_entity(node.left, current_uri)
        right_value, right_entity = evaluate_subexpression_with_entity(node.right, current_uri)

        left_value = float(left_value) if is_float(left_value) else 0
        right_value = float(right_value) if is_float(right_value) else 0

        if node.value.__contains__("COMP_>"):
            return (left_entity if left_value > right_value else right_entity), None
        elif node.value.__contains__("COMP_<"):
            return (left_entity if left_value < right_value else right_entity), None
        elif node.value.__contains__("COMP_="):
            return (left_entity if left_value == right_value else "Values are not equal"), None
        else:
            raise ValueError(f"Unrecognized COMPARE operation: {node.value}")
    # For other nodes, defer to the existing evaluation logic
    return evaluate_tree(node, current_uri)


def evaluate_subexpression_with_entity(node, current_uri=None):
    if node.value == "JOIN":
        right_answer, right_uri = evaluate_subexpression_with_entity(node.right, current_uri)
        if right_answer is None:
            right_answer = ''

        left_question = re.sub(r"Ans#\d+", right_answer, node.left.left.value)
        node.left.left.value = left_question  # Update left question with answer
        left_answer, left_uri = evaluate_subexpression_with_entity(node.left, right_uri)
        return left_answer, left_uri  # left_answer should hold the numeric value, left_uri the entity

    elif node.value in {"TextQA", "KGQA1", "KGQA2"}:
        query = node.left.value
        if node.value == "TextQA":
            answer, top_n_answer = sh_code_main.textQA(query, current_uri)
            return answer, top_n_answer
        elif node.value == "KGQA1":
            answer, uri = sh_code_main.KGQA1(query, globals.global_author_uri)
            return answer, uri
        elif node.value == "KGQA2":
            answer, uri = sh_code_main.KGQA2(query, current_uri)
            return answer, uri
    # If it's a basic value node, just return it
    return node.value, None


def evaluate_tree(node, current_uri=None):
    if node.value == "JOIN":
        right_answer, right_uri = evaluate_tree(node.right, current_uri)
        # Replace the "Ans#" placeholder in the left node's question with the right_answer
        if right_answer is None:
            right_answer = ''
        left_question = re.sub(r"Ans#\d+", right_answer, node.left.left.value)
        node.left.left.value = left_question
        left_answer, left_uri = evaluate_tree(node.left, right_uri)

        if left_answer is None:
            left_answer = ''
        return left_answer, left_uri

    elif node.value.startswith("COMP_"):
        return evaluate_with_tracking(node, current_uri)

    elif node.value == "AND":
        # Evaluate both sides and return True if both are "true"
        left_answer, _ = evaluate_tree(node.left, current_uri)
        right_answer, _ = evaluate_tree(node.right, current_uri)

        return "true" if left_answer == "true" and right_answer == "true" else "false", None

    elif node.value == "UNION":
        # Evaluate both sides and combine answers
        left_answer, _ = evaluate_tree(node.left, current_uri)
        right_answer, _ = evaluate_tree(node.right, current_uri)
        union_result = list(set([left_answer, right_answer]))  # Using a set to avoid duplicates
        return union_result, None

    elif node.value in {"TextQA", "KGQA1", "KGQA2"}:
        # Evaluate function nodes
        query = node.left.value
        if node.value == "TextQA":
            answer, top_n_answer = sh_code_main.textQA(query, current_uri)
            return answer, top_n_answer
        elif node.value == "KGQA1":
            if globals.global_author_uri:
                current_uri = globals.global_author_uri
            answer, current_uri = sh_code_main.KGQA1(query, current_uri)
            return answer, current_uri
        elif node.value == "KGQA2":
            answer, current_uri = sh_code_main.KGQA2(query, current_uri)
            return answer, current_uri
    # If the node is a raw text, return it as is
    return node.value, None