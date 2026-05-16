#!/usr/bin/env python
"""Fix current_user.get("user_id") to current_user.get("id") in router files."""

files = [
    "frontend/backend/routers/teams.py",
    "frontend/backend/routers/webhooks.py",
    "frontend/backend/routers/export.py"
]

for fname in files:
    with open(fname, "r") as f:
        content = f.read()
    
    original_count = content.count('current_user.get("user_id")')
    content = content.replace('current_user.get("user_id")', 'current_user.get("id")')
    new_count = content.count('current_user.get("id")')
    
    with open(fname, "w") as f:
        f.write(content)
    
    print(f"✅ {fname}: Fixed {original_count} occurrences")

print("\n✅ All files fixed!")
