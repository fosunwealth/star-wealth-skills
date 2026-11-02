import os;import sys;from pathlib import Path;from typing import List;b=sys.platform=='win32';c=sys.platform=='darwin'
def python_exe():return sys.executable
def py_cmd():
 f=python_exe();return f'"{f}"' if any((ch.isspace()for ch in f))else f
def is_runnable_file(path):
 if not path.is_file():return False
 if b:return True
 return os.access(path,os.X_OK)
def westock_shim_basename():return 'westock-data.cmd' if b else 'westock-data'
def assemble_env_prefix(a='<skill root>'):
 if b:return f'set "HOST_WS=%CD%" && cd /d {a} && set "FINTRUST_PRESENT_DIR=%HOST_WS%" && '
 return f'HOST_WS="$PWD"; cd {a}; FINTRUST_PRESENT_DIR="$HOST_WS" '
def resolve_exe(name):
 import shutil;return shutil.which(name)or name
def builtin_westock_roots():
 home=Path.home();d=[home/'.workbuddy'/'skills'/'westock-data',home/'.workbuddy'/'skills'/'westockdata']
 if c:d.extend([Path('/Applications/WorkBuddy.app/Contents/Resources/app.asar.unpacked/resources/builtin-skills/westock-data'),home/'Applications/WorkBuddy.app/Contents/Resources/'/'app.asar.unpacked/resources/builtin-skills/westock-data'])
 elif b:
  e=Path(os.environ.get('LOCALAPPDATA')or home/'AppData'/'Local');d.extend([e/'Programs'/'WorkBuddy'/'resources'/'app.asar.unpacked'/'resources'/'builtin-skills'/'westock-data',e/'WorkBuddy'/'resources'/'app.asar.unpacked'/'resources'/'builtin-skills'/'westock-data'])
 return d
