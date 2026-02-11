# AST_Knowledge_Graph_Round_Trip_Engine

## Overview

**AST_Knowledge_Graph_Round_Trip_Engine** is a lightweight Python library for **round-tripping Python source code through a graph representation**:

1. **Parse Python source → AST → Knowledge Graph** (`KnowledgeGraph.py`)
2. **Reconstruct Knowledge Graph → AST** (`ConstructAST.py`)
3. *(Optional)* **Unparse AST → Python source** (via `ast.unparse`)

The core idea is to represent program structure as a set of **typed nodes** and **labeled edges** (a simple knowledge graph) that is easier to analyze, transform, store, or feed into downstream tooling than raw AST objects.

This repo contains two main modules:

* `KnowledgeGraph.py`: AST → graph extractor (a custom `ast.NodeVisitor`)
* `ConstructAST.py`: graph → AST rehydrator

---

## Why this exists

Use this project when you want to:

* Build a **code knowledge graph** for static analysis, indexing, or ML features
* Apply transformations on a graph structure and then **rebuild valid Python AST**
* Persist program structure as JSON-serializable primitives (`nodes` dict + `edges` list)
* Compare code by structure (graph diffs) rather than raw text

---

## Requirements

* Python 3.9+ recommended (for `ast.unparse`)
* No third‑party dependencies (stdlib only)

---

## Data Model

### Nodes

Nodes are stored in a dictionary:

```python
nodes[node_id] = {
  "type": "<NodeType>",
  "attributes": { ... }
}
```

Common node types include (non-exhaustive):

* `Function`, `AsyncFunction`, `Class`
* `Statement`
* `Parameter`
* `Expression`, `Name`, `Literal`, `Alias`

### Edges

Edges are stored as a list of triples:

```python
edges.append((source_id, relation, destination_id))
```

Examples of relations:

* `Has_def`, `Has_class`, `Has_method`
* `Has_Statement`
* `Has_Parameter`
* `Target`, `Iterator`, `Value`, `Slice`, etc.
* Indexed relations such as `Decorator_0`, `Arg_1`, `Element_2`

The graph is rooted at a synthetic module node:

* `"Module:<top>"`

---

## Usage

### 1) Parse Python source into a Knowledge Graph

```python
import ast
from KnowledgeGraph import KnowledgeGraph

source = """
class A:
    def f(self, x: int) -> int:
        return x + 1
"""

tree = ast.parse(source)
kg = KnowledgeGraph()
kg.visit(tree)

nodes = kg.nodes
edges = kg.edges

print(len(nodes), "nodes")
print(len(edges), "edges")
```

### 2) Reconstruct an AST from the Knowledge Graph

```python
import ast
from ConstructAST import ConstructAST

builder = ConstructAST(nodes, edges)
module_ast = builder.build_module()

# Pretty-print / regenerate code (Python 3.9+)
print(ast.unparse(module_ast))
```

### 3) End-to-end round-trip example

```python
import ast
from KnowledgeGraph import KnowledgeGraph
from ConstructAST import ConstructAST

source = "x = 1\nprint(x)\n"

# Source -> AST -> Graph
kg = KnowledgeGraph()
kg.visit(ast.parse(source))

# Graph -> AST -> Source
rebuilt = ConstructAST(kg.nodes, kg.edges).build_module()
print(ast.unparse(rebuilt))
```

---

## How the extractor works (`KnowledgeGraph.py`)

`KnowledgeGraph` subclasses `ast.NodeVisitor` and walks the Python AST.

During traversal it:

* Creates stable node IDs (e.g., `Function_0`, `Parameter_3`, `Statement_12`)
* Tracks context with an internal stack (`self.stack`) and container state (`self.container`)
* Emits structural edges (`Has_Statement`, `Has_Parameter`, etc.) and semantic edges (e.g., operator relationships)
* Tracks counters for many AST constructs (functions, calls, imports, loops, literals, etc.)

Statements are attached to the correct container (module/function/class) using `statement_container()`.

---

## How reconstruction works (`ConstructAST.py`)

`ConstructAST` takes the `(nodes, edges)` graph and:

* Converts edges into an adjacency map for fast lookup
* Rebuilds expressions, statements, functions, and classes from node types + attributes
* Preserves ordering using recorded `lineno` / `order` fields and indexed edge relations
* Returns a valid `ast.Module` from `build_module()` and runs `ast.fix_missing_locations()`
