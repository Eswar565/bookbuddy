import sys, os
sys.path.insert(0, os.path.abspath('.'))
from app import app
from flask import request

with app.test_request_context('/gallery/'):
    # Check before_request funcs
    print("Testing before_request:")
    for f in app.before_request_funcs.get(None, []):
        res = f()
        if res is not None:
            print(f"Intercepted by before_request func: {f.__name__} -> {type(res)}")
            break
    else:
        # Check endpoint
        rule, args = app.url_map.bind('localhost:5001').match('/gallery/')
        print(f"Matched rule: {rule}, args: {args}")
        view_func = app.view_functions[rule]
        print(f"View func: {view_func}")
