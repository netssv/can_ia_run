import ast

with open("src/caniarun/models.py", "r") as f:
    source = f.read()

tree = ast.parse(source)

for node in tree.body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and getattr(node.targets[0], 'id', '') == 'MODELS':
        elements = node.value.elts
        print(f"Total models: {len(elements)}")
        
        families = {}
        for el in elements:
            for kw in el.keywords:
                if kw.arg == 'family':
                    family = kw.value.value
                    families[family] = families.get(family, 0) + 1
                    
        print("Models per family:")
        for f, count in sorted(families.items(), key=lambda x: x[1], reverse=True):
            print(f"  {f}: {count} models (~{count * 25} lines)")
