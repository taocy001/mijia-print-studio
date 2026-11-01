"""Owner-scoped print-file cleanup; task identities survive to prevent replay."""
import re
from pathlib import Path

TERMINAL = {'done','cancelled','aborted','rejected'}
NAME = re.compile(r'prints/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.(jpg|oc)')


def references(job):
    return {item[key] for item in [job,*job.get('pages',[])] for key in ('file','ocFile') if item.get(key)}


def safe_file(data, name):
    if not isinstance(name,str) or not NAME.fullmatch(name):raise ValueError('Invalid print filename')
    path=Path(data)/name;root=Path(data)/'prints'
    if root.is_symlink() or path.is_symlink() or path.resolve().parent!=root.resolve():raise ValueError('Invalid print path')
    return path


def plan(data, jobs, owner, keep):
    candidates=[j for j in jobs if j.get('owner')==owner and j.get('phase') in TERMINAL]
    protected=set(keep)
    for job in jobs:
        if not any(job is candidate for candidate in candidates):protected.update(references(job))
    while True:
        safe=[]
        for job in candidates:
            names=references(job)
            try:
                for name in names:safe_file(data,name)
                valid=not names.intersection(protected)
            except ValueError:valid=False
            if valid:safe.append(job)
            else:protected.update(names)
        if len(safe)==len(candidates):break
        candidates=safe
    files=set().union(*(references(j) for j in candidates)) if candidates else set()
    total=0;count=0
    for name in files:
        try:total+=safe_file(data,name).stat().st_size;count+=1
        except FileNotFoundError:pass
    return candidates,files,dict(bytes=total,files=count,jobs=len(candidates))


def clear(core, owner, keep):
    jobs,files,_=plan(core.data,core.jobs,owner,keep)
    previous=[(job,job.get('filesCleared'),job.get('cleanupPending')) for job in jobs]
    for job in jobs:job.update(filesCleared=True,cleanupPending=sorted(references(job)))
    try:core.save()
    except Exception:
        for job,cleared,pending in previous:
            if cleared is None:job.pop('filesCleared',None)
            else:job['filesCleared']=cleared
            if pending is None:job.pop('cleanupPending',None)
            else:job['cleanupPending']=pending
        raise
    removed=set();freed=0;count=0
    for name in files:
        try:
            path=safe_file(core.data,name);size=path.stat().st_size;path.unlink()
            freed+=size;count+=1;removed.add(name)
        except FileNotFoundError:removed.add(name)
        except (OSError,ValueError):pass
    for job in jobs:job['cleanupPending']=[name for name in job['cleanupPending'] if name not in removed]
    core.save()
    return dict(ok=True,bytes=freed,files=count,pending=len(files-removed)),removed
