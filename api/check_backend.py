import sys
import os
# Add current directory to path
sys.path.append(os.getcwd())

try:
    from index import app
    print("SUCCESS: Imports successful.")
    print("Routes registered:")
    for route in app.routes:
        print(f" - {route.path} {route.methods}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
