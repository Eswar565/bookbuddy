import sys, os, inspect
sys.path.insert(0, os.path.abspath('.'))
import app
endpoint = app.app.view_functions['index']
render_site = endpoint.__closure__[0].cell_contents
print("render_site module:", render_site.__module__)
print("render_site source:")
print(inspect.getsource(render_site))
