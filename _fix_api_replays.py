with open('/mnt/d/Python/Balthier/simulator/web/routes/api_replays.py', 'r', newline='') as f:
    content = f.read()

print(f"Before: {content.count('actor_id=m.group(1).strip()')} old-style refs")

# Replace each pattern (CRLF line endings)
content = content.replace(
    '                actor_id=m.group(1).strip(),\r\n                actor_name=m.group(1).strip(),\r\n                detail="Fall Back",',
    '                actor_id=meta.get("actor_id", m.group(1).strip()),\r\n                actor_name=m.group(1).strip(),\r\n                detail="Fall Back",'
)
content = content.replace(
    '                actor_id=m.group(1).strip(),\r\n                actor_name=m.group(1).strip(),\r\n                target_id=m.group(2).strip(),\r\n                target_name=m.group(2).strip(),\r\n                detail="Already at target",',
    '                actor_id=meta.get("actor_id", m.group(1).strip()),\r\n                actor_name=m.group(1).strip(),\r\n                target_id=m.group(2).strip(),\r\n                target_name=m.group(2).strip(),\r\n                detail="Already at target",'
)
content = content.replace(
    '                actor_id=m.group(1).strip(),\r\n                actor_name=m.group(1).strip(),\r\n            ),\r\n        ),\r\n        # "X moved to (a, b)"',
    '                actor_id=meta.get("actor_id", m.group(1).strip()),\r\n                actor_name=m.group(1).strip(),\r\n            ),\r\n        ),\r\n        # "X moved to (a, b)"'
)
content = content.replace(
    '                actor_id=m.group(1).strip(),\r\n                actor_name=m.group(1).strip(),\r\n                position_after={"x": int(m.group(2)), "y": int(m.group(3))},',
    '                actor_id=meta.get("actor_id", m.group(1).strip()),\r\n                actor_name=m.group(1).strip(),\r\n                position_after={"x": int(m.group(2)), "y": int(m.group(3))},'
)
content = content.replace(
    '                actor_id=m.group(1).strip(),\r\n                actor_name=m.group(1).strip(),\r\n                result_value=float(m.group(2)),\r\n            ),\r\n        ),\r\n        # "PlayerName gained N VP"',
    '                actor_id=meta.get("target_id", m.group(1).strip()),\r\n                actor_name=m.group(1).strip(),\r\n                result_value=float(m.group(2)),\r\n            ),\r\n        ),\r\n        # "PlayerName gained N VP"'
)
content = content.replace(
    '                actor_id=m.group(1).strip(),\r\n                actor_name=m.group(1).strip(),\r\n                target_id=m.group(2).strip(),\r\n                target_name=m.group(2).strip(),\r\n                detail="No valid path",',
    '                actor_id=meta.get("actor_id", m.group(1).strip()),\r\n                actor_name=m.group(1).strip(),\r\n                target_id=m.group(2).strip(),\r\n                target_name=m.group(2).strip(),\r\n                detail="No valid path",'
)
content = content.replace(
    '                actor_id=m.group(1).strip(),\r\n                actor_name=m.group(1).strip(),\r\n                detail=f"Could not move to ({m.group(2)}, {m.group(3)})",',
    '                actor_id=meta.get("actor_id", m.group(1).strip()),\r\n                actor_name=m.group(1).strip(),\r\n                detail=f"Could not move to ({m.group(2)}, {m.group(3)})",'
)

print(f"After: {content.count('actor_id=m.group(1).strip()')} old-style refs")

with open('/mnt/d/Python/Balthier/simulator/web/routes/api_replays.py', 'w', newline='') as f:
    f.write(content)
print("Done")
