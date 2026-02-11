import ast
from collections import defaultdict

class ConstructAST:
   
    def __init__(self, nodes, edges):
        self.nodes = nodes
        self.edges = edges
        self.edge_dict = defaultdict(list)

        self.operation_map = {
            "Add": ast.Add,
            "Sub": ast.Sub,
            "Mult": ast.Mult,
            "Div": ast.Div,
            "Mod": ast.Mod,
            "Pow": ast.Pow,
            "FloorDiv": ast.FloorDiv,
        }

        self.convert_edges_to_dict()

    def convert_edges_to_dict(self):
        
        for source, relation, destination in self.edges:
            self.edge_dict[(source, relation)].append(destination)

    def children(self, src, rel):
        
        return self.edge_dict.get((src, rel), [])

    def one(self, source, relation, optional=False):
        
        destination = self.edge_dict.get((source, relation), [])
        if not destination:
            if optional:
                return None
        
        return destination[0]

    def many(self, source, relation):
        
        return self.edge_dict.get((source, relation), [])

    def children_by_prefix(self, source, prefix):
        
        output = []
        for (current_source, current_relation), current_destinations in self.edge_dict.items():
            if current_source == source and current_relation.startswith(prefix):
                idx = int(current_relation.split("_", 1)[1])
                for destination in current_destinations:
                    output.append((idx, destination))
        output.sort(key=lambda x: x[0])
        
        return output

    def statement_order(self, statement_id):
        
        attributes = self.nodes[statement_id]["attributes"]
        if isinstance(attributes, dict):
            return attributes.get("order", attributes.get("lineno", None))
        
        return None

    def edge_dict_extraction(self, expression_id, relation_name):

        output = []
        for (source, relation), destinations in self.edge_dict.items():
            if source == expression_id and relation.startswith(relation_name):
                idx = int(relation.split("_", 1)[1])
                for destination in destinations:
                    output.append((idx, destination))
        output.sort(key=lambda x: x[0])

        return output

    def literal_value_extraction(self, statement_id):

        name_edges = self.children_by_prefix(statement_id, "Name_")
        names = []
        for _, literal_id in name_edges:
            literal_name = self.nodes[literal_id]["attributes"]
            names.append(str(literal_name.get("literal_value", literal_name)))

        return names

    def build_alias(self, alias_id):
        
        alias = self.nodes[alias_id]["attributes"]
        name = str(alias["name"])
        asname = str(alias["asname"]) if alias.get("asname") else None
        
        return ast.alias(name=name, asname=asname)

    def build_target(self, expression_id):
        
        node = self.nodes[expression_id]
        node_type = node["type"]
        attributes = node["attributes"]

        if node_type == "Expression" and isinstance(attributes, dict) and attributes.get("type") == "starred":
            value_id = self.one(expression_id, "Value")
            
            return ast.Starred(
                value=self.build_target(value_id),
                ctx=ast.Store()
            )

        if node_type == "Name":
            name = attributes.get("name", attributes)
            
            return ast.Name(id=str(name), ctx=ast.Store())

        if node_type == "Expression" and isinstance(attributes, dict) and attributes.get("type") == "attribute":
            value_id = self.one(expression_id, "Value")
            attribute_name = attributes.get("attribute_value")
   
            return ast.Attribute(
                value=self.build_expression(value_id),
                attr=str(attribute_name),
                ctx=ast.Store()
            )

        if node_type == "Expression" and isinstance(attributes, dict) and attributes.get("type") == "subscript":
            value_id = self.one(expression_id, "Value")
            slice_id = self.one(expression_id, "Slice")
            
            return ast.Subscript(
                value=self.build_expression(value_id),
                slice=self.build_expression(slice_id),
                ctx=ast.Store()
            )

        if node_type == "Expression" and isinstance(attributes, dict) and attributes.get("type") == "tuple":
            elements = self.children_by_prefix(expression_id, "Element_")
            
            return ast.Tuple(
                elts=[self.build_target(element) for _, element in elements],
                ctx=ast.Store()
            )

        if node_type == "Expression" and isinstance(attributes, dict) and attributes.get("type") == "list":
            elements = self.children_by_prefix(expression_id, "Element_")
            
            return ast.List(
                elts=[self.build_target(element) for _, element in elements],
                ctx=ast.Store()
            )

    def build_name(self, name_id):
        
        attributes = self.nodes[name_id]["attributes"]
        name = str(attributes.get("name", attributes))
        
        return ast.Name(id=name, ctx=ast.Load())

    def def_order(self, node_id):
   
        node = self.nodes.get(node_id, {})
        attributes = node.get("attributes", {})
        order = attributes.get("order", None)
        lineno = attributes.get("lineno", None)
        if order:
            return order
        if lineno:
            return lineno
        
        return None

    #->ast.AST
    def to_del_target(self, expression):
   
        if isinstance(expression, ast.Name):
            expression.ctx = ast.Del()
            
            return expression

        if isinstance(expression, ast.Attribute):
            expression.ctx = ast.Del()
            
            return expression

        if isinstance(expression, ast.Subscript):
            expression.ctx = ast.Del()
            
            return expression

        if isinstance(expression, ast.Starred):
            expression.ctx = ast.Del()
            expression.value = self.to_del_target(expression.value)
            
            return expression

        if isinstance(expression, ast.Tuple):
            expression.ctx = ast.Del()
            expression.elts = [self.to_del_target(element) for element in expression.elts]
            
            return expression

        if isinstance(expression, ast.List):
            expression.ctx = ast.Del()
            expression.elts = [self.to_del_target(element) for element in expression.elts]
            
            return expression
    
        return expression

    def build_excepthandler(self, handler_id):
        
        node = self.nodes[handler_id]
        type_id = self.one(handler_id, "Type", optional=True)
        name_id = self.one(handler_id, "Name", optional=True)

        element_type = self.build_expression(type_id) if type_id is not None else None

        name = None
        if name_id is not None:
            attributes = self.nodes[name_id]["attributes"]
            name = attributes.get("literal_value", attributes)

        body_ids = sorted(self.many(handler_id, "Body_Statement"), key=self.statement_order)
        body = [self.build_statement(body_id) for body_id in body_ids] or [ast.Pass()]

        return ast.ExceptHandler(type=element_type, name=name, body=body)

    def build_expression(self, expression_id):
        
        node = self.nodes[expression_id]
        node_type = node["type"]
        attributes = node["attributes"]

        if node_type == "Name":
            return self.build_name(expression_id)

        if node_type == "Literal":
            value = attributes.get("literal_value", attributes)
            
            return ast.Constant(value=value)

        if node_type == "Expression" and isinstance(attributes, dict):
            element_type = attributes.get("type")

            if element_type == "binary_operator":
                operation_id = self.one(expression_id, "Operation")
                operation_name = self.nodes[operation_id]["attributes"]["operation"]
                operation_operator = self.operation_map.get(operation_name)

                left_id = self.one(expression_id, "Left")
                right_id = self.one(expression_id, "Right")
                
                return ast.BinOp(
                    left=self.build_expression(left_id),
                    op=operation_operator(),
                    right=self.build_expression(right_id),
                )

            if element_type == "generator_expression":
                element_id = self.one(expression_id, "Element")

                generator_edges = self.edge_dict_extraction(self, expression_id, "Gen_")
                generators = [self.build_expression(generator_id) for _, generator_id in generator_edges] 
                element = self.build_expression(element_id)

                return ast.GeneratorExp(elt=element, generators=generators)

            if element_type == "set":
                element_list = self.children_by_prefix(expression_id, "Element_")
                elements = [self.build_expression(destination) for _, destination in element_list]
                
                return ast.Set(elts=elements)

            if element_type == "named_expression":
                target_id = self.one(expression_id, "Target")
                value_id = self.one(expression_id, "Value")
                target = self.build_target(target_id)
                value = self.build_expression(value_id)

                return ast.NamedExpr(target=target, value=value)

            if element_type == "starred":
                value_id = self.one(expression_id, "Value")
                value = self.build_expression(value_id)
                
                return ast.Starred(value=value, ctx=ast.Load())

            if element_type == "await":
                value_id = self.one(expression_id, "Value")
                value = self.build_expression(value_id)
                
                return ast.Await(value=value)

            if element_type == "yield":
                value_id = self.one(expression_id, "Value", optional=True)
                value = self.build_expression(value_id)
                
                return ast.Yield(value=value)

            if element_type == "yieldfrom":
                value_id = self.one(expression_id, "Value")
                
                return ast.YieldFrom(
                    value=self.build_expression(value_id)
                )

            if element_type == "lambda":
                
                parameters = self.edge_dict_extraction(expression_id, "Parameter_")
                arg_nodes = []
                parameter_id_to_default = {}

                for _, parameter_id in parameters:
                    parameter = self.nodes[parameter_id]["attributes"]
                    name = str(parameter.get("name", parameter))
                    arg_nodes.append(ast.arg(arg=name))
                    parameter_id_to_default[parameter_id] = self.one(parameter_id, "Default", optional=True)

                default_ids = [parameter_id_to_default[parameter_id] for _, parameter_id in parameters]
                number_of_defaults = sum(1 for default in default_ids if default is not None)
                tail = default_ids[-number_of_defaults:] if number_of_defaults else []
                defaults = [self.build_expression(default) for default in tail] if number_of_defaults else []

                args = ast.arguments(
                    posonlyargs=[],
                    args=arg_nodes,
                    variable_arg=None,
                    kwonlyargs=[],
                    keyword_defaults=[],
                    keyword_arg=None,
                    defaults=defaults,
                )

                body_id = self.one(expression_id, "Body")
                
                return ast.Lambda(args=args, body=self.build_expression(body_id))

            if element_type == "setcomp":
                element_id = self.one(expression_id, "Element")
                generator_edges = self.edge_dict_extraction(self, expression_id, "Gen_")
                generators = [self.build_expression(generator_id) for _, generator_id in generator_edges]
                element = self.build_expression(element_id)

                return ast.SetComp(
                    elt=element,
                    generators=generators
                )

            if element_type == "dictcomp":
                key_id = self.one(expression_id, "Key")
                value_id = self.one(expression_id, "Value")
                generator_edges = self.edge_dict_extraction(self, expression_id, "Gen_")
                generators = [self.build_expression(generator_id) for _, generator_id in generator_edges]
                key = self.build_expression(key_id)
                value = self.build_expression(value_id)

                return ast.DictComp(
                    key=key,
                    value=value,
                    generators=generators
                )

            if element_type == "slice":
                lower_id = self.one(expression_id, "Lower", optional=True)
                upper_id = self.one(expression_id, "Upper", optional=True)
                step_id = self.one(expression_id, "Step", optional=True)
                lower = self.build_expression(low_id)
                upper = self.build_expression(up_id)
                step = self.build_expression(step_id)

                return ast.Slice(lower=lower, upper=upper, step=step)

            if element_type == "attribute":
                value_id = self.one(expression_id, "Value")
                attribute_name = str(attributes.get("attribute_value", None))
                value = self.build_expression(value_id)

                return ast.Attribute(value=value, attr=attribute_name, ctx=ast.Load())

            if element_type == "call":
                function_id = self.one(expression_id, "Function_call")
                arg_edges = self.children_by_prefix(expression_id, "Arg_")
                args = [self.build_expression(destination) for _, destination in arg_edges]
                keywords = []
                key_edges = self.children_by_prefix(expression_id, "KeywordKey_")
                value_edges = self.children_by_prefix(expression_id, "KeywordValue_")

                for (key_idx, key_id), (value_idx, value_id) in zip(key_edges, value_edges):
                    keyword_name = str(self.nodes[key_id]["attributes"]["literal_value"])
                    value = self.build_expression(value_id)
                    keywords.append(ast.keyword(arg=keyword_name, value=value))

                starred_edges = self.children_by_prefix(expression_id, "KeywordStar_")
                for _, value_id in starred_edges:
                    starred_value = self.build_expression(value_id)
                    keywords.append(ast.keyword(arg=None, value=starred_value))
                
                function = self.build_expression(function_id)
                
                return ast.Call(func=function, args=args, keywords=keywords)

            if element_type == "subscript":
                value_id = self.one(expression_id, "Value")
                slice_id = self.one(expression_id, "Slice")
                value = self.build_expression(value_id)
                slice_ = self.build_expression(slice_id)
                
                return ast.Subscript(value=value, slice=slice_, ctx=ast.Load())

            if element_type == "tuple":
                element_list = self.children_by_prefix(expression_id, "Element_")
                elements = [self.build_expression(destination) for _, destination in element_list]
                
                return ast.Tuple(elts=elements, ctx=ast.Load())

            if element_type == "list":
                element_list = self.children_by_prefix(expression_id, "Element_")
                elements = [self.build_expression(destination) for _, destination in element_list]
                
                return ast.List(elts=elements, ctx=ast.Load())

            if element_type == "dict":
                pairs = []
                for (source, relation), destinations in self.edge_dict.items():
                    if source == expression_id and (relation.startswith("Key_") or relation.startswith("Value_")):
                        tag, idx = relation.split("_", 1)
                        idx = int(idx)
                        for destination in destinations:
                            pairs.append((idx, tag, destination))

                grouped = defaultdict(dict)
                for idx, tag, destination in pairs:
                    grouped[idx][tag] = destination

                keys = []
                values = []
                for idx in sorted(grouped):
                    key_id = grouped[idx].get("Key")
                    value_id = grouped[idx].get("Value")
                    keys.append(self.build_expression(key_id))
                    values.append(self.build_expression(value_id))

                return ast.Dict(keys=keys, values=values)

            if element_type == "joinedstr":
                destinations = self.edge_dict_extraction(expression_id, "Value_")
                values = [self.build_expression(destination) for _, destination in destinations]

                return ast.JoinedStr(values=values)

            if element_type == "formatted_value":
                value_id = self.one(expression_id, "Value")
                format_id = self.one(expression_id, "FormatSpecification", optional=True)
                value = self.build_expression(value_id)
                format_specification = self.build_expression(format_id) if format_id is not None else None

                return ast.FormattedValue(value=value, conversion=-1, format_spec=format_specification)

            if element_type == "if_expression":
                condition_id = self.one(expression_id, "Condition")
                condition = self.build_expression(condition_id)
                body_id = self.one(expression_id, "Body")
                body = self.build_expression(body_id)
                or_else_id = self.one(expression_id, "OrElse")
                or_else = self.build_expression(or_else_id)

                return ast.IfExp(test=condition, body=body, orelse=or_else)

            if element_type == "boolop":
                operation_id = self.one(expression_id, "Operation")
                operation_name = self.nodes[operation_id]["attributes"]["operation"]
                operation_operator = {"And": ast.And, "Or": ast.Or}.get(operation_name)
                destinations = self.edge_dict_extraction(expression_id, "Value_")
                values = [self.build_expression(destination) for _, destination in destinations]

                return ast.BoolOp(op=operation_operator(), values=values)

            if element_type == "listcomp":
                element_id = self.one(expression_id, "Element")
                element = self.build_expression(element_id)
                generator_edges = self.edge_dict_extraction(expression_id, "Gen_")
                generators = [self.build_expression(generator_id) for _, generator_id in generator_edges]

                return ast.ListComp(element=element, generators=generators)

            if element_type == "comprehension":
                target_id = self.one(expression_id, "Target")
                iterator_id = self.one(expression_id, "Iterator")
                if_edges = self.edge_dict_extraction(expression_id, "If_")

                is_async_id = self.one(expression_id, "IsAsync", optional=True)
                is_async_val = 0
                if is_async_id is not None:
                    literal_id = self.nodes[is_async_id]["attributes"]
                    is_async_val = 1 if (isinstance(literal_id, dict) and literal_id.get("literal_value")) else 0

                target = self.build_target(target_id)
                iterator = self.build_expression(iterator_id)
                ifs = [self.build_expression(destination) for _, destination in if_edges]

                return ast.comprehension(target=target, iter=iterator, ifs=ifs, is_async=is_async_val)

            if element_type == "unaryop":
                operation_id = self.one(expression_id, "Operation")
                operation_name = self.nodes[operation_id]["attributes"]["operation"]
                operation_operator = {
                    "Not": ast.Not,
                    "USub": ast.USub,
                    "UAdd": ast.UAdd,
                    "Invert": ast.Invert,
                }.get(operation_name)
                operandefault_id = self.one(expression_id, "Operand")
                operand = self.build_expression(operandefault_id)

                return ast.UnaryOp(op=operation_operator(), operand=operand)

            if element_type == "lambda":
 
                parameters = self.edge_dict_extraction(expression_id, "Parameter_")
                args = [ast.arg(arg=str(self.nodes[parameter_id]["attributes"]["name"])) for _, parameter_id in parameters]
                
                args = ast.arguments(posonlyargs=[], args=args, variable_arg=None, kwonlyargs=[], keyword_defaults=[], keyword_arg=None, defaults=[])
                body_id = self.one(expression_id, "Body")
                body = self.build_expression(body_id)

                return ast.Lambda(args=args, body=body)

            if element_type == "compare":
                left_id = self.one(expression_id, "Left")
                left = self.build_expression(left_id)

                operators = []
                comparators = []

                operator_pairs = []
                comparator_pairs = []

                for (source, relation), destinations in self.edge_dict.items():
                    if source == expression_id:
                        if relation.startswith("Op_"):
                            idx = int(relation.split("_", 1)[1])
                            for destination in destinations:
                                operator_pairs.append((idx, destination))
                        elif relation.startswith("Comparator_"):
                            idx = int(relation.split("_", 1)[1])
                            for destination in destinations:
                                comparator_pairs.append((idx, destination))

                operator_pairs.sort(key=lambda x: x[0])
                comparator_pairs.sort(key=lambda x: x[0])

                operator_map = {
                    "Eq": ast.Eq,
                    "NotEq": ast.NotEq,
                    "Lt": ast.Lt,
                    "LtE": ast.LtE,
                    "Gt": ast.Gt,
                    "GtE": ast.GtE,
                    "Is": ast.Is,
                    "IsNot": ast.IsNot,
                    "In": ast.In,
                    "NotIn": ast.NotIn,
                }

                for (_, operation_id), (_, comparator_id) in zip(operator_pairs, comparator_pairs):
                    operation_name = self.nodes[operation_id]["attributes"]["operation"]
                    operation_operator = operator_map.get(operation_name)
                    operators.append(operation_operator())
                    comparators.append(self.build_expression(comparator_id))

                return ast.Compare(left=left, ops=operators, comparators=comparators)

        return None

    def build_withitem(self, item_id):
        
        context_id = self.one(item_id, "Context")
        context_expression = self.build_expression(ctx_id)
        target_id = self.one(item_id, "Target", optional=True)
        target = self.build_target(target_id)

        return ast.withitem(context_expr=context_expression, optional_vars=target)

    #-> ast.arg
    def build_arg(self, parameter_id):
        
        parameter = self.nodes[parameter_id]["attributes"]
        name = str(parameter.get("name", parameter))
        annotation_id = self.one(parameter_id, "Annotation", optional=True)
        annotation = self.build_expression(annotation_id) if annotation_id else None
        
        return ast.arg(arg=name, annotation=annotation)

    def build_any_function(self, function_id):
        
        function_type = self.nodes[function_id]["type"]
        if function_type == "AsyncFunction":
            
            return self.build_functionlike(function_id, is_async=True)
        
        return self.build_functionlike(function_id, is_async=False)

    def build_statement(self, statement_id):
        
        statement_node = self.nodes[statement_id]
        statement_type = statement_node["type"]
        attributes = statement_node["attributes"]

        if statement_type != "Statement" or not isinstance(attributes, dict):
            
            return ast.Pass()

        kind = attributes.get("kind")

        if kind == "Pass":
            
            return ast.Pass()

        if kind == "Delete":
            target_edges = self.children_by_prefix(statement_id, "Target_")
            targets = []
            for _, target_id in target_edges:
                target = self.build_expression(target_id)
                targets.append(self.to_del_target(target))
            
            return ast.Delete(targets=targets)

        if kind == "Global":
            names = self.literal_value_extraction(statement_id)
            
            return ast.Global(names=names)

        if kind == "Nonlocal":
            names = self.literal_value_extraction(statement_id)
            
            return ast.Nonlocal(names=names)

        if kind == "While":
            condition_id = self.one(statement_id, "Condition")
            body_ids = sorted(self.many(statement_id, "Body_Statement"), key=self.statement_order)
            or_else_ids = sorted(self.many(statement_id, "OrElse_statement"), key=self.statement_order)

            condition = self.build_expression(test_id)
            body = [self.build_statement(body_id) for body_id in body_ids] or [ast.Pass()]
            or_else = [self.build_statement(or_else_id) for or_else_id in or_else_ids]

            return ast.While(test=condition, body=body, orelse=or_else)

        if kind == "With":
            item_edges = self.children_by_prefix(statement_id, "Item_")
            items = [self.build_withitem(item_id) for _, item_id in item_edges]
            body_ids = sorted(self.many(statement_id, "Body_Statement"), key=self.statement_order)
            body = [self.build_statement(body_id) for body_id in body_ids] or [ast.Pass()]

            return ast.With(items=items, body=body)

        if kind == "Assert":
            condition_id = self.one(statement_id, "Condition")
            condition = self.build_expression(condition_id)
            message_id = self.one(statement_id, "Message", optional=True)
            message = self.build_expression(message_id)

            return ast.Assert(test=condition, msg=message)

        if kind == "Try":
            body_ids = sorted(self.many(statement_id, "Body_Statement"), key=self.statement_order)
            or_else_ids = sorted(self.many(statement_id, "OrElse_Statement"), key=self.statement_order)
            final_body_ids = sorted(self.many(statement_id, "FinalBody_Statement"), key=self.statement_order)
            handler_edges = self.children_by_prefix(statement_id, "Handler_")
            handlers = [self.build_excepthandler(handler_id) for _, handler_id in handler_edges]
            body = [self.build_statement(body_id) for body_id in body_ids] or [ast.Pass()]
            or_else = [self.build_statement(or_else_id) for or_else_id in or_else_ids]
            final_body = [self.build_statement(final_body_id) for final_body_id in final_body_ids]

            return ast.Try(body=body, handlers=handlers, orelse=or_else, finalbody=final_body)

        if kind == "Raise":
            exception_id = self.one(statement_id, "Exception", optional=True)
            exception = self.build_expression(exception_id)
            cause_id = self.one(statement_id, "Cause", optional=True)
            cause = self.build_expression(cause_id)

            return ast.Raise(exc=exception, cause=cause)

        if kind == "Import":
            alias_edges = self.children_by_prefix(statement_id, "Alias_")
            names = [self.build_alias(alias_edge) for _, alias_edge in alias_edges]
            
            return ast.Import(names=names)

        if kind == "ImportFrom":
            module_id = self.one(statement_id, "Module", optional=True)
            level_id = self.one(statement_id, "Level", optional=True)

            module = None
            if module_id:
                attributes = self.nodes[module_id]["attributes"]
                module = str(attributes.get("literal_value", attributes))

            level = 0
            if level_id:
                attributes = self.nodes[level_id]["attributes"]
                level = int(attributes.get("literal_value", attributes))

            alias_edges = self.children_by_prefix(statement_id, "Alias_")
            names = [self.build_alias(alias_edge) for _, alias_edge in alias_edges]
            
            return ast.ImportFrom(module=module, names=names, level=level)

        if kind == "AugAssign":
            target_ids = self.children(statement_id, "Target")
            target = self.build_target(target_ids[0])
            value_ids = self.children(statement_id, "Value")
            value = self.build_expression(value_ids[0])
            operation_id = self.one(statement_id, "Operation")
            operation_name = self.nodes[operation_id]["attributes"]["operation"]
            operation_operator = self.operation_map.get(operation_name)

            return ast.AugAssign(target=target, op=operation_operator(), value=value)

        if kind == "AnnAssign":
            target_id = self.one(statement_id, "Target")
            target = self.build_target(target_id)
            annotation_id = self.one(statement_id, "Annotation")
            annotation = self.build_expression(annotation_id)
            value_id = self.one(statement_id, "Value", optional=True)
            value = self.build_expression(val_id)
            simple_id = self.one(statement_id, "Simple", optional=True)

            simple = 1
            if simple_id:
                attributes = self.nodes[simple_id]["attributes"]
                simple = int(attributes.get("literal_value", 1))

            return ast.AnnAssign(target=target, annotation=annotation, value=value, simple=simple)

        if kind == "Break":
            
            return ast.Break()

        if kind == "Continue":
            
            return ast.Continue()

        if kind == "For":
            target_id = self.one(statement_id, "Target")
            target = self.build_target(target_id)
            iterator_id = self.one(statement_id, "Iterator")
            iterator = self.build_expression(iterator_id)
            body_ids = sorted(self.many(statement_id, "Body_Statement"), key=self.statement_order)
            body = [self.build_statement(body_id) for body_id in body_ids] or [ast.Pass()]
            or_else_ids = sorted(self.many(statement_id, "OrElse_Statement"), key=self.statement_order)
            or_else = [self.build_statement(or_else_id) for or_else_id in or_else_ids]

            return ast.For(target=target, iter=iterator, body=body, orelse=or_else, type_comment=None)

        if kind == "AsyncFor":
            target_id = self.one(statement_id, "Target")
            target = self.build_target(target_id)
            iterator_id = self.one(statement_id, "Iterator")
            iterator = self.build_expression(iterator_id)
            body_ids = sorted(self.many(statement_id, "Body_statement"), key=self.statement_order)
            body = [self.build_statement(body_id) for body_id in body_ids] or [ast.Pass()]
            or_else_ids = sorted(self.many(statement_id, "Orelse_statement"), key=self.statement_order)
            or_else = [self.build_statement(or_else_id) for or_else_id in or_else_ids]

            return ast.AsyncFor(target=target, iter=iterator, body=body, orelse=or_else, type_comment=None)

        if kind == "Return":
            expression_ids = self.children(statement_id, "Computes")
            if len(expression_ids) == 0:
                
                return ast.Return(value=None)
            expression_value = self.build_expression(expression_ids[0])
            
            return ast.Return(value=expression_value)

        if kind == "Assign":
            target_ids = self.children(statement_id, "Target")
            targets = [self.build_target(target_id) for target_id in target_ids]
            value_ids = self.children(statement_id, "Value")
            value = self.build_expression(value_ids[0])
            
            return ast.Assign(targets=targets, value=value)

        if kind == "ExpressionStatement":
            value_ids = self.children(statement_id, "Value")
            if not value_ids:
                return ast.Expr(value=ast.Constant(value=None))
            value = self.build_expression(value_ids[0])
            
            return ast.Expr(value=value)

        if kind == "If":
            condition_ids = self.children(statement_id, "Condition")
            condition = self.build_expression(condition_ids[0])
            body_ids = self.children(statement_id, "Body_Statement")
            or_else_ids = self.children(statement_id, "OrElse_Statement")
            body_ids = sorted(body_ids, key=self.statement_order)
            body = [self.build_statement(body_id) for body_id in body_ids] or [ast.Pass()]
            or_else_ids = sorted(or_else_ids, key=self.statement_order)
            or_else = [self.build_statement(or_else_id) for or_else_id in or_else_ids]

            return ast.If(test=condition, body=body, orelse=or_else)

        return ast.Pass()

    def build_functionlike(self, function_id, is_async):
        function_name = self.nodes[function_id]["attributes"]["name"]
        parameter_ids = self.edge_dict.get((function_id, "Has_Parameter"), [])
        position_only_parameters = []
        position_parameters = []
        keyword_only_parameters = []
        variable_arg_parameter_id = None
        keyword_arg_parameter_id = None

        for parameter_id in parameter_ids:
            parameter = self.nodes[parameter_id]["attributes"]
            kind = parameter.get("kind", "arg")
            name = str(parameter.get("name", parameter))
            position = int(parameter.get("position", 0))

            if kind == "PositionOnly":
                position_only_parameters.append((position, name, parameter_id))
            elif kind == "KeywordOnly":
                keyword_only_parameters.append((position, name, parameter_id))
            elif kind == "VariableArg":
                variable_arg_parameter_id = parameter_id
            elif kind == "KeywordArg":
                keyword_arg_parameter_id = parameter_id
            else:
                position_parameters.append((position, name, parameter_id))

        position_only_parameters.sort(key=lambda x: x[0])
        position_parameters.sort(key=lambda x: x[0])
        keyword_only_parameters.sort(key=lambda x: x[0])

        position_only_args = [self.build_arg(parameter_id) for _, _, parameter_id in position_only_parameters]
        position_args     = [self.build_arg(parameter_id) for _, _, parameter_id in position_parameters]
        keyword_only_args  = [self.build_arg(parameter_id) for _, _, parameter_id in keyword_only_parameters]

        variable_arg = self.build_arg(variable_arg_parameter_id) if variable_arg_parameter_id is not None else None
        keyword_arg  = self.build_arg(keyword_arg_parameter_id) if keyword_arg_parameter_id is not None else None

        combined_position = position_only_parameters + position_parameters

        parameter_id_to_default = {parameter_id: self.one(parameter_id, "Default", optional=True) for _, _, parameter_id in combined_position}

        defaults_sum = sum(1 for value in parameter_id_to_default.values() if value is not None)
        tail = combined_position[-defaults_sum:] if defaults_sum else []

        position_defaults = []
        missing = []
        for _, _, parameter_id in tail:
            default_id = parameter_id_to_default.get(parameter_id)
            if default_id is None:
                missing.append(parameter_id)
            else:
                position_defaults.append(self.build_expression(default_id))

        keyword_defaults = []
        for _, _, parameter_id in keyword_only_parameters:
            default_id = self.one(parameter_id, "Default", optional=True)
            keyword_defaults.append(self.build_expression(default_id) if default_id is not None else None)

        args = ast.arguments(
            posonlyargs=position_only_args,
            args=position_args,
            vararg=variable_arg,            
            kwonlyargs=keyword_only_args,
            kw_defaults=keyword_defaults,    
            kwarg=keyword_arg,               
            defaults=position_defaults,
        )

        body_items = []

        statement_ids = self.edge_dict.get((function_id, "Has_Statement"), [])
        for statement_id in statement_ids:
            body_items.append(("statement", statement_id, self.statement_order(statement_id)))

        function_define_ids = (self.edge_dict.get((function_id, "Has_def"), []))
        for function_define_id in function_define_ids:
            body_items.append(("def", function_define_id, self.def_order(function_define_id)))

        body_items.sort(key=lambda x: (x[2], x[1]))

        body = []
        for kind, identity, _ in body_items:
            if kind == "statement":
                body.append(self.build_statement(identity))
            else:
                node_type = self.nodes[identity]["type"]
                if node_type in ("Function", "AsyncFunction"):
                    body.append(self.build_any_function(identity))
                elif node_type == "Class":
                    body.append(self.build_class(identity))
                else:
                    body.append(ast.Pass())

        if not body:
            body = [ast.Pass()]


        decorator_edges = self.children_by_prefix(function_id, "Decorator_")
        decorators = [self.build_expression(decorator) for _, decorator in decorator_edges]

        if is_async:
            
            return ast.AsyncFunctionDef(
                name=function_name,
                args=args,
                body=body,
                decorator_list=decorators,
                returns=None,
                type_comment=None,
            )

        return ast.FunctionDef(
            name=function_name,
            args=args,
            body=body,
            decorator_list=decorators,
            returns=None,
            type_comment=None,
        )

    def build_class(self, class_id):
        class_name = self.nodes[class_id]["attributes"]["name"]
        base_edges = self.children_by_prefix(class_id, "Base_")
        bases = [self.build_expression(base_edge) for _, base_edge in base_edges]

        body_items = []

        statement_ids = self.edge_dict.get((class_id, "Has_Statement"),[])
        for statement_id in statement_ids:
            body_items.append(("statement", statement_id, self.statement_order(statement_id)))

        function_define_ids = self.edge_dict.get((class_id, "Has_def"), [])
        if not function_define_ids:
            method_define_ids = self.edge_dict.get((class_id, "Has_method"), [])
            function_define_id_ids = method_define_ids

        for function_define_id in function_define_ids:
            body_items.append(("def", function_define_id, self.def_order(function_define_id)))

        body_items.sort(key=lambda x: (x[2], x[1]))

        body = []
        for kind, identity, _ in body_items:
            if kind == "statement":
                body.append(self.build_statement(identity))
            else:
                node_type = self.nodes[identity]["type"]
                if node_type in ("Function", "AsyncFunction"):
                    body.append(self.build_any_function(identity))
                elif node_type == "Class":
                    body.append(self.build_class(identity))
                else:
                    body.append(ast.Pass())

        if not body:
            body = [ast.Pass()]

        decorator_edges = self.children_by_prefix(class_id, "Decorator_")
        decorators = [self.build_expression(decorator) for _, decorator in decorator_edges]

        return ast.ClassDef(
            name=class_name,
            bases=bases,
            keywords=[],
            body=body,
            decorator_list=decorators
        )

    def build_module(self):
        body_items = []

        statement_ids = self.edge_dict.get(("Module:<top>", "Has_Statement"), [])
            
        for statement_id in statement_ids:
            body_items.append(("statement", statement_id, self.statement_order(statement_id)))

        module_class_ids = self.edge_dict.get(("Module:<top>", "Has_class"), [])
        for module_class_id in module_class_ids:
            body_items.append(("class", module_class_id, self.def_order(module_class_id)))

        module_define_ids = self.edge_dict.get(("Module:<top>", "Has_def"), [])
        for module_define_id in module_define_ids:
            body_items.append(("def", module_define_id, self.def_order(module_define_id)))

        body_items.sort(key=lambda x: (x[2], x[1]))

        body = []
        for kind, identity, _ in body_items:
            if kind == "statement":
                body.append(self.build_statement(identity))
            else:
                node_type = self.nodes[identity]["type"]
                if node_type in ("Function", "AsyncFunction"):
                    body.append(self.build_any_function(identity))
                elif node_type == "Class":
                    body.append(self.build_class(identity))
                else:
                    body.append(ast.Pass())

        try:
            module = ast.Module(body=body, type_ignores=[])
        except TypeError:
            module = ast.Module(body=body)

        return ast.fix_missing_locations(module)