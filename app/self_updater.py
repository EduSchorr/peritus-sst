from __future__ import annotations
import argparse, os, shutil, subprocess, sys, time, zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath

ROOT=Path(__file__).resolve().parent.parent
UPDATES=ROOT/'atualizacoes'; BACKUPS=ROOT/'backups'; APP=ROOT/'app'
PROTECTED={'data','documentos_gerados','backups','atualizacoes','.runtime'}


def validate_package(pkg):
    with zipfile.ZipFile(pkg) as z:
        files=[PurePosixPath(n.replace('\\','/')) for n in z.namelist() if n and not n.endswith('/')]
        if not files or any(p.is_absolute() or '..' in p.parts for p in files): raise RuntimeError('Pacote inválido: caminho inseguro.')
        if not any(p.parts and p.parts[0]=='app' for p in files): raise RuntimeError('Pacote inválido: pasta app ausente.')
        if any(p.parts and p.parts[0] in PROTECTED for p in files): raise RuntimeError('Pacote tenta alterar dados protegidos.')
    return files


def wait_process(pid, timeout=45):
    if os.name=='nt':
        import ctypes
        synchronize=0x00100000
        handle=ctypes.windll.kernel32.OpenProcess(synchronize,False,int(pid or 0))
        if not handle: return
        try: ctypes.windll.kernel32.WaitForSingleObject(handle,int(timeout*1000))
        finally: ctypes.windll.kernel32.CloseHandle(handle)
        return
    end=time.time()+timeout
    while pid and time.time()<end:
        try: os.kill(pid,0)
        except OSError: return
        time.sleep(.35)


def restart_system():
    launcher=ROOT/'app'/'launcher.py'
    if os.name=='nt' and launcher.exists():
        pythonw=ROOT/'.runtime'/'Scripts'/'pythonw.exe'
        executable=pythonw if pythonw.exists() else Path(sys.executable)
        flags=getattr(subprocess,'CREATE_NO_WINDOW',0)|getattr(subprocess,'DETACHED_PROCESS',0)|getattr(subprocess,'CREATE_NEW_PROCESS_GROUP',0)
        subprocess.Popen([str(executable),str(launcher)],cwd=str(ROOT),stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=flags,close_fds=True)


def apply_package(pkg, wait_pid=None, restart=False):
    pkg=Path(pkg).resolve()
    if not pkg.exists() or pkg.parent.resolve()!=UPDATES.resolve(): raise RuntimeError('Pacote fora da pasta de atualizações.')
    files=validate_package(pkg); wait_process(wait_pid)
    stamp=datetime.now().strftime('%Y%m%d_%H%M%S'); backup=BACKUPS/f'app_{stamp}'
    BACKUPS.mkdir(exist_ok=True); shutil.copytree(APP,backup)
    try:
        with zipfile.ZipFile(pkg) as z:
            for item in files:
                target=(ROOT/Path(*item.parts)).resolve()
                if ROOT.resolve() not in target.parents: raise RuntimeError('Destino inseguro.')
                target.parent.mkdir(parents=True,exist_ok=True)
                with z.open(item.as_posix()) as src, target.open('wb') as dst: shutil.copyfileobj(src,dst)
        requirements=ROOT/'requirements.txt'
        if requirements.exists(): subprocess.run([sys.executable,'-m','pip','install','-r',str(requirements)],check=True)
        (UPDATES/'ultima_atualizacao.txt').write_text(f'{datetime.now().isoformat(timespec="seconds")} | {pkg.name}\nBackup: {backup}',encoding='utf-8')
    except Exception:
        if APP.exists(): shutil.rmtree(APP)
        shutil.copytree(backup,APP); raise
    if restart: restart_system()
    return backup


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--package',required=True); parser.add_argument('--wait-pid',type=int); parser.add_argument('--restart',action='store_true'); args=parser.parse_args()
    try: apply_package(args.package,args.wait_pid,args.restart)
    except Exception as exc:
        (UPDATES/'erro_atualizacao.txt').write_text(str(exc),encoding='utf-8')
        if args.restart:
            try: restart_system()
            except Exception as restart_exc:
                with (UPDATES/'erro_atualizacao.txt').open('a',encoding='utf-8') as log:
                    log.write(f'\nFalha ao reabrir: {restart_exc}')
        sys.exit(1)
