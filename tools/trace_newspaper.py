import sys, os
sys.path.insert(0, os.path.abspath('.'))
from app import app
from flask import request

client = app.test_client()

with app.test_request_context('/newspaper/'):
    print("Request path:", request.path)
    print("request.path.strip('/'):", request.path.strip('/'))
    for f in app.before_request_funcs.get(None, []):
        try:
            res = f()
            print(f.__name__, "result:", res is not None)
            if res is not None:
                print(f"Intercepted by {f.__name__} ->", type(res))
                break
        except Exception as e:
            print(f"Exception in {f.__name__}:", e)
            import traceback; traceback.print_exc()
            break

