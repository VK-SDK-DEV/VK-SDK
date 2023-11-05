import ast
import inspect
from dataclasses import dataclass
from itertools import zip_longest
from typing import Union
from types import CodeType
import pickle

from .imports import ImportTools
from .cmd import AfterFunc, waiters, after_func_poll, AbstractAfterFunc

WAIT_FUNC_NAME = "wait"

def parent_chain(chain_in):
    chain = chain_in.split(".")
    return ".".join(chain[:-1]+[chain[-1].split("_")[0]]) if "_" in chain[-1] else chain_in

def compare_ast(node1: Union[ast.expr, list[ast.expr]], node2: Union[ast.expr, list[ast.expr]]) -> bool:
    if type(node1) is not type(node2):
        return False

    if isinstance(node1, ast.AST):
        for k, v in vars(node1).items():
            if k in {"lineno", "end_lineno", "col_offset", "end_col_offset", "ctx"}:
                continue
            if not compare_ast(v, getattr(node2, k)):
                return False
        return True

    elif isinstance(node1, list) and isinstance(node2, list):
        return all(compare_ast(n1, n2) for n1, n2 in zip_longest(node1, node2))
    else:
        return node1 == node2


@dataclass
class Waiter:
    name: str
    func: CodeType
    node: ast.Lambda
    module: object


def find_data(func):
    func = ast.parse(inspect.getsource(func).strip(),
                     mode="exec").body[0].value
    node = func.args[1] if isinstance(
        func.args[0], ast.Constant) else func.args[0]
    for waiter in waiters:
        if compare_ast(waiter.node, node):
            # retrieve locals from stack
            stack = inspect.stack()
            for index, item in enumerate(stack[2:-1]):
                inside = stack[1+index]
                if inside[3] == "wait" and not inside.filename.endswith("vk_sdk\\wait.py"):
                    locs = item[0].f_locals
                    locs.pop("self")
                    waiter = waiters.find(lambda it: it.name == parent_chain(waiter.name))
                    return locs, waiter


def wait(user_id, func):
    locs, waiter = find_data(func)

    return AfterFunc(after_name=waiter.name, user_id=user_id,
                     locals=pickle.dumps(locs))


class WaitVisiter(ast.NodeVisitor):
    def __init__(self, code, module) -> None:
        super().__init__()
        self.code = code
        self.module = module
        self.visit_Module(code)

    def dump(self, node):
        print(ast.dump(node, indent=4))

    def visit_call(self, node: ast.Call, chain: str, counter: int):
        if isinstance(node.func, ast.Attribute) and node.func.attr == WAIT_FUNC_NAME:
            assert 0 <= len(node.args) <= 3
            match = len(node.args) == 2
            if match: match_text = node.args[0].value
            lambda_func = node.args[0] if not match else node.args[1]
            current_chain = chain+f".wait{counter}{'' if not match else '_'+match_text}"

            evaluted = compile(ast.Expression(
                body=lambda_func), filename="", mode="eval")

            waiters.append(Waiter(name=current_chain,
                           func=evaluted, node=lambda_func, module=self.module))
            # circular support?
            
            pc = parent_chain(current_chain)
            af = AbstractAfterFunc(
                pc, None, None)
            if match:
                assert isinstance(node.args[0], ast.Constant)
                af.text_matchers[match_text] = evaluted
            else:
                af.text_matchers["default"] = evaluted
            after_func_poll[pc] = af
            # visit inners
            cnt = 0
            if isinstance(lambda_func.body, ast.Call):
                self.visit_call(lambda_func.body, current_chain, 0)
            elif isinstance(lambda_func.body, ast.Tuple):
                for inner in lambda_func.body.elts:
                    if isinstance(inner, ast.Call):
                        self.visit_call(inner,
                                                   current_chain, cnt)
            counter += 1 and not match

    def visit_Module(self, node: ast.Module):
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and hasattr(item, "name"):
                counter = 0
                for inside in item.body:
                    if isinstance(inside, ast.Expr) and isinstance(inside.value, ast.Call):
                        self.visit_call(inside.value,
                                                   str(item.name), counter)
        self.generic_visit(node)


@ImportTools.on_module()
def on_module_ast(module, source):
    WaitVisiter(ast.parse(source), module)
