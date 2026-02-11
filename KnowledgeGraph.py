import ast 
from typing import Optional

class KnowledgeGraph(ast.NodeVisitor):

    def __init__(self):
        
        self.nodes = {}
        self.edges = []
        self.stack = []
        self.container = []
        self.class_count = 0
        self.function_count = 0
        self.parameter_count = 0
        self.binary_operator_count = 0
        self.operation_count = 0
        self.return_count = 0
        self.name_count = 0
        self.literal_count = 0
        self.other_count = 0
        self.statement_count = 0
        self.assign_count = 0
        self.expression_statement_count = 0
        self.if_count = 0
        self.attribute_count = 0
        self.call_count = 0
        self.subscript_count = 0
        self.tuple_count = 0
        self.dictionary_count = 0
        self.list_count = 0
        self.for_count = 0
        self.asyncfor_count = 0
        self.augassign_count = 0
        self.import_count = 0
        self.importfrom_count = 0
        self.alias_count = 0
        self.lambda_count = 0
        self.slice_count = 0
        self.try_count = 0
        self.except_count = 0
        self.raise_count = 0
        self.assert_count = 0
        self.set_count = 0
        self.dictcomp_count = 0
        self.setcomp_count = 0
        self.with_count = 0
        self.while_count = 0
        self.global_count = 0
        self.nonlocal_count = 0
        self.pass_count = 0
        self.delete_count = 0
        self.asyncfunction_count = 0
        self.async_function_count = 0
        self.annassign_count = 0
        self.with_count = 0
        self.with_item_count = 0 
        self.break_count = 0
        self.generator_count = 0
        self.starred_count = 0
        self.named_expression_count = 0
        self.yield_count = 0
        self.await_count = 0
        self.generator_expression_count = 0
        self.joined_string_count = 0
        self.list_comp_count = 0
        self.formatted_value_count = 0
        self.bool_operation_count = 0
        self.unary_count = 0
        self.compare_count = 0
        self.if_expression_count = 0
        

    def add_node(self, node_id, node_type, attributes):

        self.nodes[node_id] = {"type": node_type, "attributes": attributes}

    def add_edge(self, source, relation, destination):

        self.edges.append((source, relation, destination))

    def statement_container(self):
        
        if self.container:
            return self.container[-1]

        if self.stack:
            top = self.stack[-1]
            top_type = self.nodes[top]["type"]

            if top_type in ("Function", "AsyncFunction"):
                return (top, "Has_Statement")

            if top_type == "Class":
                return (top, "Has_Statement")

        return ("Module:<top>", "Has_Statement")

    def add_statement(self, statement_id, kind, lineno=None):
    
        order = lineno if lineno is not None else self.statement_count
        self.add_node(statement_id, "Statement", {"kind": kind, "lineno": lineno, "order": order})
        container_id, relation = self.statement_container()
        self.add_edge(container_id, relation, statement_id)
        self.statement_count += 1

    def add_alias(self, name: str, asname: Optional[str]):
        
        alias_id = f"alias_{self.alias_count}"
        self.alias_count += 1
        self.add_node(alias_id, "Alias", {"name": name, "asname": asname})
        
        return alias_id

    def attach_param_annotation(self, parameter_id, arg_node, function_id):
        
        if getattr(arg_node, "annotation", None) is not None:
            annotation_id = self.handle_expression(arg_node.annotation, function_id=None)
            self.add_edge(parameter_id, "Annotation", annotation_id)

    def get_function_id(self):

        return self.stack[-1] if self.stack else None

    def process_parameter_args(self, function_node, function_id):

        args = getattr(function_node, "args", None)
        position = 0
        ordered_position_parameter_ids = []  

        for arg in getattr(args, "posonlyargs", []):
            parameter_id = f"Parameter_{self.parameter_count}"
            self.add_node(parameter_id, "Parameter", {"name": arg.arg, "position": position, "kind": "PositionOnly"})
            self.add_edge(function_id, "Has_Parameter", parameter_id)
            ordered_position_parameter_ids.append(parameter_id)
            self.attach_param_annotation(parameter_id, arg, function_id)
            self.parameter_count += 1
            position += 1

        for arg in getattr(args, "args", []):
            parameter_id = f"Parameter_{self.parameter_count}"
            self.add_node(parameter_id, "Parameter", {"name": arg.arg, "position": position, "kind": "arg"})
            self.add_edge(function_id, "Has_Parameter", parameter_id)
            self.attach_param_annotation(parameter_id, arg, function_id)
            ordered_position_parameter_ids.append(parameter_id)
            self.parameter_count += 1
            position += 1

        vararg = getattr(args, "vararg", None)
        if vararg is not None:
            parameter_id = f"Parameter_{self.parameter_count}"
            self.add_node(parameter_id, "Parameter", {"name": vararg.arg, "position": 0, "kind": "VariableArg"})
            self.add_edge(function_id, "Has_Parameter", parameter_id)
            self.attach_param_annotation(parameter_id, vararg, function_id)
            self.parameter_count += 1

        ordered_kwonly_param_ids = []
        for idx, arg in enumerate(getattr(args, "kwonlyargs", [])):
            parameter_id = f"Parameter_{self.parameter_count}"
            self.add_node(parameter_id, "Parameter", {"name": arg.arg, "position": idx, "kind": "KeywordOnly"})
            self.add_edge(function_id, "Has_Parameter", parameter_id)
            self.attach_param_annotation(parameter_id, arg, function_id)
            ordered_kwonly_param_ids.append(parameter_id)
            self.parameter_count += 1

        kwarg = getattr(args, "kwarg", None)
        if kwarg is not None:
            parameter_id = f"Parameter_{self.parameter_count}"
            self.add_node(parameter_id, "Parameter", {"name": kwarg.arg, "position": 0, "kind": "KeywordArg"})
            self.add_edge(function_id, "Has_Parameter", parameter_id)
            self.attach_param_annotation(parameter_id, kwarg, function_id)
            self.parameter_count += 1

        defaults = getattr(args, "defaults", None)
        defaults = list(defaults) if defaults else None
        if defaults:
            start = len(ordered_position_parameter_ids) - len(defaults)
            for idx, default_expression in enumerate(defaults):
                parameter_id = ordered_position_parameter_ids[start + idx]
                default_id = self.handle_expression(default_expression, function_id)
                self.add_edge(parameter_id, "Default", default_id)

        for parameter_id, default_expression in zip(ordered_kwonly_param_ids, getattr(args, "kw_defaults", None)):
            if default_expression is not None:
                default_id = self.handle_expression(default_expression, function_id)
                self.add_edge(parameter_id, "Default", default_id)

        for idx, decorator in enumerate(getattr(function_node, "decorator_list", [])):
            decorator_id = self.handle_expression(decorator, function_id)
            self.add_edge(function_id, f"Decorator_{idx}", decorator_id)

    def process_for_statements(self, for_node, function_id, for_id):

        target = getattr(for_node, "target", None)
        iterator = getattr(for_node, "iter", None)
        if target:
            target_id = self.handle_expression(target, function_id)
            self.add_edge(for_id, "Target", target_id)

        if iterator:
            iterator_id = self.handle_expression(iterator, function_id)
            self.add_edge(for_id, "Iterator", iterator_id)

        self.container.append((for_id, "Body_Statement"))
        body = getattr(for_node, "body", [])
        for statement in body:
            self.visit(statement)
        self.container.pop()

        self.container.append((for_id, "OrElse_Statement"))
        or_else = getattr(for_node, "orelse", [])
        for statement in or_else:
            self.visit(statement)
        self.container.pop()    

    def visit_Import(self, import_node):
        import_id = f"import_{self.import_count}"
        self.import_count += 1
        self.add_statement(import_id, "Import", lineno=getattr(import_node, "lineno", None))

        names = getattr(import_node, "names", [])
        for idx, name in enumerate(names):
            alias_name = getattr(name, "name", None)
            alias_asname = getattr(name, "asname", None)
            alias_id = self.add_alias(alias_name, alias_asname)
            self.add_edge(import_id, f"Alias_{idx}", alias_id)

    def visit_ImportFrom(self, import_from_node):
        import_from_id = f"importfrom_{self.importfrom_count}"
        self.importfrom_count += 1
        self.add_statement(import_from_id, "ImportFrom", lineno=getattr(import_from_node, "lineno", None))

        module_name = getattr(import_from_node, "module", "")
        module_literal = f"literal_{self.literal_count}"
        self.literal_count += 1
        self.add_node(module_literal, "Literal", {"literal_value": module_name})
        self.add_edge(import_from_id, "Module", module_literal)

        module_level = getattr(import_from_node, "level", 0)
        level_literal = f"literal_{self.literal_count}"
        self.literal_count += 1
        self.add_node(level_literal, "Literal", {"literal_value": int(module_level)})
        self.add_edge(import_from_id, "Level", level_literal)

        names = getattr(import_from_node, "names", [])
        for idx, alias in enumerate(names):
            alias_name = getattr(alias, "name", None)
            alias_asname = getattr(alias, "asname", None)
            alias_id = self.add_alias(alias_name, alias_asname)
            self.add_edge(import_from_id, f"Alias_{idx}", alias_id)

    def visit_ClassDef(self, class_node):
        
        class_id = f"class_{self.class_count}"
        self.class_count += 1

        lineno = getattr(class_node, "lineno", None)
        order = lineno if lineno is not None else self.statement_count
        self.add_node(class_id, "Class", {"name": class_node.name, "lineno": lineno, "order": order})

        for idx, base in enumerate(class_node.bases):
            base_id = self.handle_expression(base, function_id=None)
            self.add_edge(class_id, f"Base_{idx}", base_id)

        if self.stack and self.nodes[self.stack[-1]]["type"] == "Class":
            self.add_edge(self.stack[-1], "Has_class", class_id)  
        else:
            self.add_edge("Module:<top>", "Has_class", class_id)  

        for idx, decorator in enumerate(class_node.decorator_list):
            decorator_id = self.handle_expression(decorator, function_id=None)
            self.add_edge(class_id, f"Decorator_{idx}", decorator_id)

        self.stack.append(class_id)
        self.generic_visit(class_node)
        self.stack.pop()

    def visit_FunctionDef(self, function_node):
        
        function_id = f"Function_{self.function_count}"
        lineno = getattr(function_node, "lineno", None)
        order = lineno if lineno is not None else self.statement_count
        self.add_node(function_id, "Function", {"name": function_node.name, "lineno": lineno, "order": order})
        self.function_count += 1

        if self.stack:
            parent = self.stack[-1]
            parent_type = self.nodes[parent]["type"]

            if parent_type == "Class":
                self.add_edge(parent, "Has_def", function_id) 
            elif parent_type == "Function":
                self.add_edge(parent, "Has_def", function_id) 
            else:
                self.add_edge("Module:<top>", "Has_def", function_id)
        else:
            self.add_edge("Module:<top>", "Has_def", function_id)

        self.process_parameter_args(function_node, function_id)

        self.stack.append(function_id)
        self.generic_visit(function_node)
        self.stack.pop()

    def visit_AsyncFunctionDef(self, async_function_node):
        function_id = f"AsyncFunction_{self.async_function_count}"
        lineno = getattr(async_function_node, "lineno", None)
        order = lineno if lineno is not None else self.statement_count
        self.add_node(function_id, "AsyncFunction", {"name": function_node.name, "lineno": lineno, "order": order})
        self.async_function_count += 1

        if self.stack:
            parent = self.stack[-1]
            parent_type = self.nodes[parent]["type"]

            if parent_type == "Class":
                self.add_edge(parent, "Has_Async_Function", function_id)
                # self.add_edge(parent, "Has_def", function_id)     # unify defs list
            elif parent_type in ("Function", "AsyncFunction"):
                self.add_edge(parent, "Has_Async_Function", function_id) 
            else:
                self.add_edge("Module:<top>", "Has_Async_Function", function_id)
        else:
            self.add_edge("Module:<top>", "Has_Async_Function", function_id)

        self.process_parameter_args(async_function_node)

        self.stack.append(function_id)
        self.generic_visit(function_node)
        self.stack.pop()

    def visit_Return(self, return_object):
        function_id = self.get_function_id()
        return_id = f"return_{self.return_count}"
        self.return_count += 1
        self.add_statement(return_id, "Return", lineno=getattr(return_object, "lineno", None))
        
        function_type = self.nodes.get(function_id, None)
        function_type = function_type.get("type") if function_type else None
        if function_id and (function_type == "Function" or function_type == "AsyncFunction"):
            self.add_edge(function_id, "Returns", return_id)

        return_object_value = getattr(return_object, "value", None)
        if return_object_value is not None:
            expression_id = self.handle_expression(return_object_value, function_id)
            self.add_edge(return_id, "Computes", expression_id)

    def visit_Pass(self, pass_node):
        pass_id = f"pass_{self.pass_count}"
        self.pass_count += 1
        self.add_statement(pass_id, "Pass", lineno=getattr(pass_node, "lineno", None))

    def visit_Delete(self, delete_node):
        function_id = self.get_function_id()
        delete_id = f"delete_{self.delete_count}"
        self.delete_count += 1

        self.add_statement(delete_id , "Delete", lineno=getattr(delete_node, "lineno", None))

        targets = getattr(delete_node, "targets", [])
        for idx, target in enumerate(targets):
            target_id = self.handle_expression(target, function_id)
            self.add_edge(delete_id, f"Target_{idx}", target_id)

    def visit_Global(self, global_node):
        global_id = f"global_{self.global_count}"
        self.global_count += 1

        self.add_statement(global_id, "Global", lineno=getattr(global_node, "lineno", None))

        names = getattr(global_node, "names", [])
        for idx, name in enumerate(names):
            literal_id = f"literal_{self.literal_count}"
            self.literal_count += 1
            self.add_node(literal_id, "Literal", {"literal_value": str(name)})
            self.add_edge(global_id, f"Name_{idx}", literal_id)

    def visit_Nonlocal(self, non_local_node):
        non_local_id = f"nonlocal_{self.nonlocal_count}"
        self.nonlocal_count += 1

        self.add_statement(non_local_id, "Nonlocal", lineno=getattr(non_local_node, "lineno", None))

        names = getattr(non_local_node, "names", [])
        for i, name in enumerate(names):
            literal_id = f"literal_{self.literal_count}"
            self.literal_count += 1
            self.add_node(literal_id, "Literal", {"literal_value": str(name)})
            self.add_edge(non_local_id, f"Name_{idx}", literal_id)

    def visit_While(self, while_node):
        function_id = self.get_function_id()
        while_id = f"while_{self.while_count}"
        self.while_count += 1
        self.add_statement(while_id, "While", lineno=getattr(while_node, "lineno", None))

        condition = getattr(while_node, "test", None)
        if condition:
            condition_id = self.handle_expression(condition, function_id)
            self.add_edge(while_id, "Condition", condition_id)

        self.container.append((while_id, "Body_Statement"))
        body = getattr(while_node, "body", [])
        for statement in body:
            self.visit(statement)
        self.container.pop()

        self.container.append((while_id, "OrElse_Statement"))
        or_else = getattr(while_node, "orelse", [])
        for statement in orelse:
            self.visit(statement)
        self.container.pop()

    def visit_Raise(self, raise_node):
        function_id = self.get_function_id()
        raise_id = f"raise_{self.raise_count}"
        self.raise_count += 1
        self.add_statement(raise_id, "Raise", lineno=getattr(raise_node, "lineno", None))

        exception = getattr(raise_node, "exc", None)
        if exception:
            exception_id = self.handle_expression(exception, function_id)
            self.add_edge(raise_id, "Exception", exception_id)

        cause = getattr(raise_node, "cause", None)
        if cause:
            cause_id = self.handle_expression(cause, function_id)
            self.add_edge(raise_id, "Cause", cause_id)

    def visit_Try(self, try_node):
        function_id = self.get_function_id()
        try_id = f"try_{self.try_count}"
        self.try_count += 1
        self.add_statement(try_id, "Try", lineno=getattr(try_node, "lineno", None))

        self.container.append((try_id, "Body_Statement"))
        body = getattr(try_node, "body", [])
        for statement in body:
            self.visit(statement)
        self.container.pop()

        handlers = getattr(try_node, "handlers", [])
        for idx, handler in enumerate(handlers):
            handler_id = f"except_{self.except_count}"
            self.except_count += 1
            self.add_node(handler_id, "ExceptHandler", {"order": idx})
            self.add_edge(try_id, f"Handler_{idx}", handler_id)

            handler_type = getattr(handler, "type", None)
            if handler_type:
                type_id = self.handle_expression(handler.type, function_id)
                self.add_edge(handler_id, "Type", type_id)
            
            handler_name = getattr(handler, "name", None)
            if h.name:
                name_literal = f"literal_{self.literal_count}"
                self.literal_count += 1
                self.add_node(name_literal, "Literal", {"literal_value": str(handler_name)})
                self.add_edge(handler_id, "Name", name_literal)

            self.container.append((handler_id, "Body_Statement"))
            body = getattr(handler, "body", [])
            for statement in body:
                self.visit(statement)
            self.container.pop()

        self.container.append((try_id, "OrElse_Statement"))
        or_else = getattr(try_node, "orelse", [])
        for statement in or_else:
            self.visit(statement)
        self.container.pop()

        self.container.append((try_id, "FinalBody_Statement"))
        final_body = getattr(try_node, "finalbody", [])
        for statement in final_body:
            self.visit(statement)
        self.container.pop()

    def visit_Assert(self, assert_node):
        function_id = self.get_function_id()
        assert_id = f"assert_{self.assert_count}"
        self.assert_count += 1
        self.add_statement(assert_id, "Assert", lineno=getattr(assert_node, "lineno", None))

        condition = getattr(assert_node, "test", None)
        if condition:
            condition_id = self.handle_expression(condition, function_id)
            self.add_edge(assert_id, "Condition", condition_id)

        message = getattr(assert_node, "msg", None)
        if message:
            message_id = self.handle_expression(message, function_id)
            self.add_edge(assert_id, "Message", message_id)

    def visit_Assign(self, assign_node):
        
        function_id = self.get_function_id()
        assign_id = f"assign_{self.assign_count}"
        self.assign_count += 1
        self.add_statement(assign_id, "Assign", lineno=getattr(assign_node, "lineno", None))

        targets = getattr(assign_node, "targets", [])
        for target in targets:
            target_id = self.handle_expression(target, function_id)
            self.add_edge(assign_id, "Target", target_id)

        assign_value = getattr(assign_node, "value", None)
        if assign_value:
            value_id = self.handle_expression(assign_value, function_id)
            self.add_edge(assign_id, "Value", value_id)

    def visit_AugAssign(self, aug_assign_node):
        function_id = self.get_function_id()
        augment_id = f"augassign_{self.augassign_count}"
        self.augassign_count += 1
        self.add_statement(augment_id, "AugAssign", lineno=getattr(aug_assign_node, "lineno", None))
        
        target = getattr(aug_assign_node, "target", None)
        if target:
            target_id = self.handle_expression(target, function_id)
            self.add_edge(augment_id, "Target", target_id)

        operation = getattr(aug_assign_node, "op", None)
        if operation:
            operation_name = type(operation).__name__
            operation_id = f"operation_{self.operation_count}"
            self.operation_count += 1
            self.add_node(operation_id, "Operation", {"operation": operation_name})
            self.add_edge(augment_id, "Operation", operation_id)

        aug_value = getattr(aug_assign_node, "value", None)
        if aug_value:
            value_id = self.handle_expression(aug_value, function_id)
            self.add_edge(augment_id, "Value", value_id)

    def visit_AnnAssign(self, ann_assign_node):
        function_id = self.get_function_id()
        annotation_id = f"annassign_{self.annassign_count}"
        self.annassign_count += 1
        self.add_statement(ann_id, "AnnAssign", lineno=getattr(ann_assign_node, "lineno", None))

        target = getattr(ann_assign_node, "target", None)
        if target:
            target_id = self.handle_expression(target, function_id)
            self.add_edge(ann_id, "Target", target_id)

        annotation = getattr(ann_assign_node, "annotation", None)
        if annotation:
            ann_expression_id = self.handle_expression(annotation, function_id=None)
            self.add_edge(ann_id, "Annotation", ann_expression_id)

        ann_value = getattr(ann_assign_node, "value", None)
        if ann_value:
            value_id = self.handle_expression(ann_value, function_id=None)
            self.add_edge(ann_id, "Value", value_id)

        ann_simple_literal = getattr(ann_assign_node, "simple", None)
        if ann_simple_literal:
            simple_literal = f"literal_{self.literal_count}"
            self.literal_count += 1
            self.add_node(simple_literal, "Literal", {"literal_value": int(ann_simple_literal)})
            self.add_edge(ann_id, "Simple", simple_literal)

    def visit_With(self, with_node):
        function_id = self.get_function_id()
        with_id = f"with_{self.with_count}"
        self.with_count += 1
        self.add_statement(with_id, "With", lineno=getattr(with_node, "lineno", None))

        with_items = getattr(with_node, "items", [])
        for idx, item in enumerate(with_items):
            item_id = f"withitem_{self.with_item_count}"
            self.with_item_count += 1
            self.add_node(item_id, "WithItem", {"order": idx})
            self.add_edge(with_id, f"Item_{idx}", item_id)

            context = getattr(item, "context_expr", None)
            if context:
                context_id = self.handle_expression(context, function_id)
                self.add_edge(item_id, "Context", context_id)

            optional_vars = getattr(item, "optional_vars", None)
            if optional_vars:
                target_id = self.handle_expression(optional_vars, function_id)
                self.add_edge(item_id, "Target", target_id)

        self.container.append((with_id, "Body_Statement"))
        body = getattr(with_node, "body", [])
        for statement in body:
            self.visit(statement)
        self.container.pop()

    def visit_Expr(self, expression_node):
       
        function_id = self.get_function_id()
        expression_statement_id = f"ExpressionStatement_{self.expression_statement_count}"
        self.expression_statement_count += 1
        self.add_statement(expression_statement_id, "ExpressionStatement", lineno=getattr(expression_node, "lineno", None))

        expression_value = getattr(expression_node, "value", None)
        if expression_value:
            value_id = self.handle_expression(expression_value, function_id)
            self.add_edge(expression_statement_id, "Value", value_id)

    def visit_For(self, for_node):
        
        function_id = self.get_function_id()
        for_id = f"for_{self.for_count}"
        self.for_count += 1
        self.add_statement(for_id, "For", lineno=getattr(for_node, "lineno", None))
        self.process_for_statements(for_node, function_id, for_id)

    def visit_AsyncFor(self, async_for_node):
        
        function_id = self.get_function_id()
        async_for_id = f"asyncfor_{self.asyncfor_count}"
        self.asyncfor_count += 1
        self.add_statement(async_for_id, "AsyncFor", lineno=getattr(async_for_node, "lineno", None))
        self.process_for_statements(async_for_node, function_id, async_for_id)

    def visit_If(self, if_node):
        
        function_id = self.get_function_id()
        if_id = f"if_{self.if_count}"
        self.if_count += 1
        self.add_statement(if_id, "If", lineno=getattr(if_node, "lineno", None))

        condition = getattr(if_node, "test", None)
        if condition:
            condition_id = self.handle_expression(if_node.test, function_id)
            self.add_edge(if_id, "Condition", condition_id)
        
        self.container.append((if_id, "Body_Statement"))
        body = getattr(if_node, "body", [])
        for statement in body:
            self.visit(statement)
        self.container.pop()

        self.container.append((if_id, "OrElse_Statement"))
        or_else = getattr(if_node, "orelse", [])
        for statement in or_else:
            self.visit(statement)
        self.container.pop()

    def visit_Break(self, break_node):
        break_id = f"break_{self.break_count}"
        self.break_count += 1
        self.add_statement(break_id, "Break", lineno=getattr(break_node, "lineno", None))

    def visit_Continue(self, continue_node):
        continue_id = f"continue_{self.continue_count}"
        self.continue_count += 1
        self.add_statement(continue_id, "Continue", lineno=getattr(continue_node, "lineno", None))

    def handle_expression(self, return_node, function_id):

        if isinstance(return_node, ast.BinOp):
            
            binary_operator_id = f"binary_operator_{self.binary_operator_count}"
            self.add_node(binary_operator_id, "Expression", {"type":"binary_operator"})
            self.binary_operator_count += 1

            operation = getattr(return_node, "op", None)
            if operation:
                operation_name = type(operation).__name__ 
                operation_id = f"operation_{self.operation_count}"
                self.add_node(operation_id, "Operation", {"operation":operation_name})
                self.operation_count += 1
                self.add_edge(binary_operator_id, "Operation", operation_id)

            left = getattr(return_node, "left", None)
            if left:
                left_id = self.handle_expression(left, function_id)
                self.add_edge(binary_operator_id, "Left", left_id)

            right = getattr(return_node, "right", None)
            if right:
                right_id = self.handle_expression(right, function_id)
                self.add_edge(binary_operator_id, "Right", right_id)

            return binary_operator_id

        if isinstance(return_node, ast.SetComp):
            
            set_comp_id = f"setcomp_{self.setcomp_count}"
            self.setcomp_count += 1
            self.add_node(set_comp_id, "Expression", {"type": "setcomp"})

            element = getattr(return_node, "elt", None)
            if element:
                element_id = self.handle_expression(element, function_id)
                self.add_edge(set_comp_id, "Element", element_id)

            generators = getattr(return_node, "generators", [])
            for idx, generator in enumerate(generators):
                generator_id = f"generator_{self.generator_count}"
                self.generator_count += 1
                self.add_node(generator_id, "Expression", {"type": "generator"})
                self.add_edge(set_comp_id, f"Gen_{idx}", generator_id)

                target = getattr(generator, "target", None)
                if target:
                    target_id = self.handle_expression(target, function_id)
                    self.add_edge(generator_id, "Target", target_id)

                iterator = getattr(generator, "iter", None)
                if iterator:
                    iterator_id = self.handle_expression(iterator, function_id)
                    self.add_edge(generator_id, "Iterator", iterator_id)

                generator_ifs = getattr(generator, "ifs", [])
                for ifs_idx, if_expression in enumerate(generator_ifs):
                    if_id = self.handle_expression(if_expression, function_id)
                    self.add_edge(generator_id, f"If_{ifs_idx}", if_id)

                async_literal = f"literal_{self.literal_count}"
                self.literal_count += 1
                self.add_node(async_literal, "Literal", {"literal_value": bool(getattr(generator, "is_async", False))})
                self.add_edge(g_id, "IsAsync", async_lit)

            return set_comp_id

        if isinstance(return_node, ast.Lambda):
            lambda_id = f"lambda_{self.lambda_count}"
            self.lambda_count += 1
            self.add_node(lambda_id, "Expression", {"type": "lambda"})

            parameter_ids = []
            args = getattr(return_node, "args", None)
            if args:
                for idx, arg in enumerate(getattr(args, "args", [])):
                    parameter_id = f"Parameter_{self.parameter_count}"
                    self.parameter_count += 1
                    parameter_arg = getattr(arg, "arg", None)
                    if parameter_arg:
                        self.add_node(parameter_id, "Parameter", {"name": parameter_arg, "position": idx, "kind": "arg"})
                        self.add_edge(lambda_id, f"Parameter_{idx}", parameter_id)
                        parameter_ids.append(parameter_id)

            defaults = getattr(args, "defaults", None)
            defaults = list(defaults) if defaults else None
            if defaults:
                start = len(parameter_ids) - len(defaults)
                for idx, default_expression in enumerate(defaults):
                    parameter_id = parameter_ids[start + idx]
                    default_id = self.handle_expression(default_expression, function_id)
                    self.add_edge(parameter_id, "Default", default_id)

            body = getattr(return_node, "body", None)
            if body:
                body_id = self.handle_expression(body, function_id)
                self.add_edge(lambda_id, "Body", body_id)

            return lambda_id

        if isinstance(return_node, ast.Set):
            set_id = f"set_{self.set_count}"
            self.set_count += 1
            self.add_node(set_id, "Expression", {"type": "set"})

            elements = getattr(return_node, "elts", [])
            for idx, element in enumerate(elements):
                element_id = self.handle_expression(element, function_id)
                self.add_edge(set_id, f"Element_{idx}", element_id)

            return set_id

        if isinstance(return_node, ast.DictComp):
            
            dictcomp_id = f"dictcomp_{self.dictcomp_count}"
            self.dictcomp_count += 1
            self.add_node(dictcomp_id, "Expression", {"type": "dictcomp"})

            key_id = self.handle_expression(return_node.key, function_id)
            value_id = self.handle_expression(return_node.value, function_id)
            self.add_edge(dictcomp_id, "Key", key_id)
            self.add_edge(dictcomp_id, "Value", value_id)

            generators = getattr(return_node, "generators", [])
            for idx, generator in enumerate(generators):
                generator_id = f"generator_{self.generator_count}"
                self.generator_count += 1
                self.add_node(generator_id, "Expression", {"type": "generator"})
                self.add_edge(dictcomp_id, f"Gen_{idx}", generator_id)

                target_id = self.handle_expression(generator.target, function_id)
                self.add_edge(generator_id, "Target", target_id)

                iterator_id = self.handle_expression(generator.iter, function_id)
                self.add_edge(generator_id, "Iter", iterator_id)

                generator_ifs = getattr(generator, "ifs", [])
                for ifs_idx, if_expression in enumerate(generators_ifs):
                    if_id = self.handle_expression(if_expression, function_id)
                    self.add_edge(generator_id, f"If_{ifs_idx}", if_id)

                async_literal = f"literal_{self.literal_count}"
                self.literal_count += 1
                self.add_node(async_literal, "Literal", {"literal_value": bool(getattr(generator, "is_async", False))})
                self.add_edge(generator_id, "IsAsync", async_literal)

            return dictcomp_id

        if isinstance(return_node, ast.Starred):
            
            starred_id = f"starred_{self.starred_count}"
            self.starred_count += 1
            self.add_node(starred_id, "Expression", {"type": "starred"})
            value_id = self.handle_expression(return_node.value, function_id)
            self.add_edge(starred_id, "Value", value_id)
            
            return star_id

        if isinstance(return_node, ast.Name):
            
            name_id = f"name_{self.name_count}"
            self.add_node(name_id, "Name", {"name":return_node.id})
            self.name_count += 1
            
            return name_id

        if isinstance(return_node, ast.Constant):
            
            literal_id = f"literal_{self.literal_count}"
            self.add_node(literal_id, "Literal", {"literal_value":return_node.value})
            self.literal_count += 1
            
            return literal_id

        if isinstance(return_node, ast.Attribute):
            
            attribute_id = f"attribute_{self.attribute_count}"
            self.attribute_count += 1
            self.add_node(attribute_id, "Expression", {"type": "attribute", "attribute_value": return_node.attr})
            base_id = self.handle_expression(return_node.value, function_id)
            self.add_edge(attribute_id, "Value", base_id)
            
            return attribute_id


        if isinstance(return_node, ast.NamedExpr):
            
            named_expression_id = f"namedexpr_{self.named_expression_count}"
            self.named_expression_count += 1
            self.add_node(named_expression_id, "Expression", {"type": "named_expression"})

            target_id = self.handle_expression(return_node.target, function_id)
            value_id = self.handle_expression(return_node.value, function_id)

            self.add_edge(named_expression_id, "Target", target_id)
            self.add_edge(named_expression_id, "Value", value_id)

            return named_expression_id

        if isinstance(return_node, ast.Yield):
            
            yield_id = f"yield_{self.yield_count}"
            self.yield_count += 1
            self.add_node(y_id, "Expression", {"type": "yield"})

            value = getattr(return_node, "value", None)
            if value:
                value_id = self.handle_expression(value, function_id)
                self.add_edge(yield_id, "Value", value_id)

            return yield_id

        if isinstance(return_node, ast.YieldFrom):
            
            yield_from_id = f"yieldfrom_{self.yield_count}"
            self.yield_count += 1
            self.add_node(yield_from_id, "Expression", {"type": "yieldfrom"})

            value = getattr(return_node, "value", None)
            if value:
                value_id = self.handle_expression(value, function_id)
                self.add_edge(yield_from_id, "Value", value_id)

            return yield_from_id

        if isinstance(return_node, ast.Await):
            
            await_id = f"await_{self.await_count}"
            self.await_count += 1
            self.add_node(await_id, "Expression", {"type": "await"})

            value = getattr(return_node, "value", None)
            if value:
                value_id = self.handle_expression(value, function_id)
                self.add_edge(await_id, "Value", value_id)

            return await_id

        if isinstance(return_node, ast.Slice):
            
            slice_id = f"slice_{self.slice_count}"
            self.slice_count += 1
            self.add_node(slice_id, "Expression", {"type": "slice"})

            lower = getattr(return_node, "lower", None)
            if lower:
                lower_id = self.handle_expression(lower, function_id)
                self.add_edge(slice_id, "Lower", lower_id)

            upper = getattr(return_node, "upper", None)
            if upper:
                upper_id = self.handle_expression(upper, function_id)
                self.add_edge(slice_id, "Upper", upper_id)

            step = getattr(return_node, "step", None)
            if step:
                step_id = self.handle_expression(step, function_id)
                self.add_edge(slice_id, "Step", step_id)

            return slice_id

        if isinstance(return_node, ast.GeneratorExp):
            
            generator_expression_id = f"generator_expression_{self.generator_expression_count}"
            self.generator_expression_count += 1
            self.add_node(generator_expression_id, "Expression", {"type": "generator_expression"})

            element_id = self.handle_expression(return_node.elt, function_id)
            self.add_edge(generator_expression_id, "Element", element_id)

            generators = getattr(return_node, "generators", [])
            for idx, generator in enumerate(return_node.generators):
                generator_id = f"generator_{self.generator_count}"
                self.generator_count += 1
                self.add_node(generator_id, "Expression", {"type": "generator"})
                self.add_edge(generator_expression_id, f"Gen_{idx}", generator_id)

                target_id = self.handle_expression(generator.target, function_id)
                self.add_edge(generator_id, "Target", target_id)

                iterator_id = self.handle_expression(generator.iter, function_id)
                self.add_edge(generator_id, "Iterator", iterator_id)

                ifs = getattr(generator, "ifs", [])
                for ifs_idx, if_expression in enumerate(ifs):
                    if_id = self.handle_expression(if_expression, function_id)
                    self.add_edge(generator_id, f"If_{ifs_idx}", if_id)

                async_literal = f"{generator_id}_async"
                self.add_node(async_literal, "Literal", {"literal_value": bool(getattr(generator, "is_async", False))})
                self.add_edge(generator_id, "IsAsync", async_literal)

            return generator_expression_id

        if isinstance(return_node, ast.Call):
            
            call_id = f"call_{self.call_count}"
            self.call_count += 1
            self.add_node(call_id, "Expression", {"type": "call"})

            function = getattr(return_node, "func", None)
            if function:
                function_expression = self.handle_expression(function, function_id)
                self.add_edge(call_id, "Function_call", function_expression)

            args = getattr(return_node, "args", [])
            for idx, arg in enumerate(args):
                arg_id = self.handle_expression(arg, function_id)
                self.add_edge(call_id, f"Arg_{idx}", arg_id)

            keywords = getattr(return_node, "keywords", [])
            for idx, keyword in enumerate(keywords):
                if keyword.arg is None:
                    value_id = self.handle_expression(keyword.value, function_id)
                    self.add_edge(call_id, f"KeywordStar_{idx}", value_id)
                else:
                    keyword_id = f"literal_{self.literal_count}"
                    self.literal_count += 1
                    self.add_node(keyword_id, "Literal", {"literal_value": keyword.arg})

                    value_id = self.handle_expression(keyword.value, function_id)
                    self.add_edge(call_id, f"KeywordKey_{idx}", keyword_id)
                    self.add_edge(call_id, f"KeywordValue_{idx}", value_id)
            
            return call_id

        if isinstance(return_node, ast.Subscript):
            
            subscript_id = f"subscript_{self.subscript_count}"
            self.subscript_count += 1
            self.add_node(subscript_id, "Expression", {"type": "subscript"})
            value_id = self.handle_expression(return_node.value, function_id)
            slice_id = self.handle_expression(return_node.slice, function_id)
            self.add_edge(subscript_id, "Value", value_id)
            self.add_edge(subscript_id, "Slice", slice_id)
            
            return subscript_id

        if isinstance(return_node, ast.Compare):
            
            compare_id = f"compare_{self.compare_count}"
            self.compare_count += 1
            self.add_node(compare_id, "Expression", {"type": "compare"})

            left = getattr(return_node, "left", None)
            if left:
                left_id = self.handle_expression(left, function_id)
                self.add_edge(compare_id, "Left", left_id)

            for idx, (operation, comparator) in enumerate(zip(return_node.ops, return_node.comparators)):
                operation_name = type(operation).__name__ 
                operation_id = f"operation_{self.operation_count}"
                self.operation_count += 1
                self.add_node(operation_id, "Operation", {"operation": operation_name})
                self.add_edge(compare_id, f"Op_{idx}", operation_id)

                comparator_id = self.handle_expression(comparator, function_id)
                self.add_edge(compare_id, f"Comparator_{idx}", comparator_id)

            return compare_id

        if isinstance(return_node, ast.Tuple):
            
            tuple_id = f"tuple_{self.tuple_count}"
            self.tuple_count += 1
            self.add_node(tuple_id, "Expression", {"type": "tuple"})
            
            elements = getattr(return_node, "elts", [])
            for idx, element in enumerate(elements):
                element_id = self.handle_expression(element, function_id)
                self.add_edge(tuple_id, f"Element_{idx}", element_id)
            
            return tuple_id

        if isinstance(return_node, ast.Dict):
            
            dictionary_id = f"dictionary_{self.dictionary_count}"
            self.dictionary_count += 1
            self.add_node(dictionary_id, "Expression", {"type": "dict"})
      
            for idx, (key, value) in enumerate(zip(return_node.keys, return_node.values)):
                if key is not None:
                    key_id = self.handle_expression(key, function_id)
                    self.add_edge(dictionary_id, f"Key_{idx}", key_id)
                value_id = self.handle_expression(value, function_id)
                self.add_edge(dictionary_id, f"Value_{idx}", value_id)
            
            return dictionary_id

        if isinstance(return_node, ast.List):
            
            list_id = f"list_{self.list_count}"
            self.list_count += 1
            self.add_node(list_id, "Expression", {"type": "list"})

            elements = getattr(return_node, "elts", [])
            for idx, element in enumerate(elements):
                element_id = self.handle_expression(element, function_id)
                self.add_edge(list_id, f"Element_{idx}", element_id)

            return list_id

        if isinstance(return_node, ast.JoinedStr):
            
            joined_string_id = f"joinedstr_{self.joined_string_count}"
            self.joined_string_count += 1
            self.add_node(joined_string_id, "Expression", {"type": "joinedstr"})
            
            values = getattr(return_node, "values", [])
            for idx, value in enumerate(values):
                value_id = self.handle_expression(value, function_id)
                self.add_edge(joined_string_id, f"Value_{idx}", value_id)
            
            return joined_string_id

        if isinstance(return_node, ast.ListComp):
            
            list_comp_id = f"listcomp_{self.list_comp_count}"
            self.list_comp_count += 1
            self.add_node(list_comp_id, "Expression", {"type": "listcomp"})

            element_id = self.handle_expression(return_node.elt, function_id)
            self.add_edge(list_comp_id, "Element", element_id)

            generators = getattr(return_node, "generators", [])
            for idx, generator in enumerate(generators):
                generator_id = f"generator_{self.generator_count}"
                self.generator_count += 1
                self.add_node(generator_id, "Expression", {"type": "generator"})
                self.add_edge(list_comp_id, f"Gen_{idx}", generator_id)

                target_id = self.handle_expression(generator.target, function_id)
                self.add_edge(generator_id, "Target", target_id)

                iterator_id = self.handle_expression(generator.iter, function_id)
                self.add_edge(generator_id, "Iterator", iterator_id)

                generator_ifs = getattr(generator, "ifs", [])
                for ifs_idx, if_expression in enumerate(generator_ifs):
                    if_id = self.handle_expression(if_expression, function_id)
                    self.add_edge(generator_id, f"If_{ifs_idx}", if_id)

                self.add_node(f"{generator_id}_async", "Literal", {"literal_value": bool(getattr(generator, "is_async", False))})
                self.add_edge(generator_id, "IsAsync", f"{generator_id}_async")

            return list_comp_id

        if isinstance(return_node, ast.FormattedValue):
            
            formatted_value_id = f"formatted_{self.formatted_value_count}"
            self.formatted_value_count += 1
            self.add_node(formatted_value_id, "Expression", {"type": "formatted_value"})
            value_id = self.handle_expression(return_node.value, function_id)
            self.add_edge(formatted_value_id, "Value", value_id)
 
            format_specification = getattr(return_node, "format_spec", None)
            if format_specification:
                format_specification_id = self.handle_expression(format_specification, function_id)
                self.add_edge(formatted_value_id, "FormatSpecification", format_specification_id)
            
            return formatted_value_id

        if isinstance(return_node, ast.BoolOp):
            
            bool_id = f"boolop_{self.bool_operation_count}"
            self.bool_operation_count += 1
            self.add_node(bool_id, "Expression", {"type": "boolop"})

            operation = getattr(return_node, "op", None)
            if operation:
                operation_name = type(operation).__name__ 
                operation_id = f"bool_operation_{self.operation_count}"
                self.operation_count += 1
                self.add_node(operation_id, "Operation", {"operation": operation_name})
                self.add_edge(bool_id, "Operation", operation_id)

            values = getattr(return_node, "values", [])
            for idx, value in enumerate(values):
                value_id = self.handle_expression(value, function_id)
                self.add_edge(bool_id, f"Value_{idx}", value_id)

            return bool_id

        if isinstance(return_node, ast.UnaryOp):
            
            unary_id = f"unaryop_{self.unary_count}"
            self.unary_count += 1
            self.add_node(unary_id, "Expression", {"type": "unaryop"})

            operation = getattr(return_node, "op", None)
            if operation:
                operation_name = type(operation).__name__ 
                operation_id = f"operation_{self.operation_count}"
                self.operation_count += 1
                self.add_node(operation_id, "Operation", {"operation": operation_name})
                self.add_edge(unary_id, "Operation", operation_id)

            operand = getattr(return_node, "operand", None)
            if operand:
                operand_id = self.handle_expression(operand, function_id)
                self.add_edge(unary_id, "Operand", operand_id)
            
            return unary_id

        if isinstance(return_node, ast.IfExp):
            
            if_expression_id = f"ifexp_{self.if_expression_count}"
            self.if_expression_count += 1
            self.add_node(if_expression_id, "Expression", {"type": "if_expression"})

            condition_id = self.handle_expression(return_node.test, function_id)
            body_id = self.handle_expression(return_node.body, function_id)
            else_id = self.handle_expression(return_node.orelse, function_id)

            self.add_edge(if_expression_id, "Condition", condition_id)
            self.add_edge(if_expression_id, "Body", body_id)
            self.add_edge(if_expression_id, "OrElse", else_id)

            return if_expression_id

        other_id = f"other_{self.other_count}"
        self.add_node(other_id, "Expression", {"name":type(return_node).__name__})
        self.other_count += 1
        
        return other_id