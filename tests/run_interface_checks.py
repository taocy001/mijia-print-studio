"""Offline status and editor regression suite."""
from pathlib import Path
import subprocess
import sys

root=Path(__file__).resolve().parents[1]
checks=['job_notifications','print_progress','print_process','detected_paper',
        'browser_settings','host_queue','dock_layout','ui_parity',
        'editor_isolation','selection_position','crop_frame_drag']
failed=[]
for name in checks:
    print('Checking '+name,flush=True)
    try:
        subprocess.run([sys.executable,str(root/'tests'/('check_'+name+'.py'))],cwd=root,check=True,timeout=180)
    except (subprocess.CalledProcessError,subprocess.TimeoutExpired):
        failed.append(name)
if failed:
    raise SystemExit('Failed: '+', '.join(failed))
print('PASS: interface regression; no physical printing')
