from backend.loader.compiler import compile_content
m = compile_content()
print(f"OK: {len(m.artifacts)} artifacts, {len(m.collisions)} collisions")
for c in m.collisions:
    print(f"  COLLISION: {c}")
