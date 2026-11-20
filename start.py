"""Double-click launcher. Checks server version before opening the app."""
import ast
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.request import build_opener, ProxyHandler
import webbrowser

ROOT=Path(__file__).resolve().parent
URL='http://127.0.0.1:8789'
LOCAL=build_opener(ProxyHandler({}))

def expected_version():
    tree=ast.parse((ROOT/'server.py').read_text(encoding='utf-8-sig'))
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='APP_VERSION' for t in node.targets):
            return ast.literal_eval(node.value)
    raise RuntimeError('Cannot determine SHOPScript version.')

def running_version():
    try:
        with LOCAL.open(URL+'/api/status',timeout=4) as r:
            data=json.load(r)
        return data.get('app_version','old-version')
    except OSError:
        return None

def main():
    expected=expected_version();actual=running_version()
    if actual is not None and actual!=expected:
        print('An older SHOPScript is using port 8789. Close the old server or restart Windows, then open SHOPScript again.')
        print('Expected:',expected,'Running:',actual)
        return 1
    if actual is None:
        flags=subprocess.CREATE_NO_WINDOW|subprocess.CREATE_NEW_PROCESS_GROUP if os.name=='nt' else 0
        with (ROOT/'server-output.log').open('ab') as output, (ROOT/'server-error.log').open('ab') as error:
            subprocess.Popen([sys.executable,'-B',str(ROOT/'server.py'),'--port','8789'],cwd=ROOT,
                stdin=subprocess.DEVNULL,stdout=output,stderr=error,close_fds=True,creationflags=flags)
        for _ in range(30):
            time.sleep(.3)
            if running_version()==expected: break
        else:
            print('SHOPScript did not start. See server-error.log.');return 1
    webbrowser.open(URL)
    return 0

if __name__=='__main__':
    raise SystemExit(main())
