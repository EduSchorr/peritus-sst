from __future__ import annotations
import shutil, subprocess, sys, zipfile
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
UPDATES=ROOT/'atualizacoes'; BACKUPS=ROOT/'backups'; APP=ROOT/'app'

def main():
    packages=sorted(UPDATES.glob('Peritus_SST_Atualizacao_*.zip'),key=lambda p:p.stat().st_mtime,reverse=True)
    if not packages:
        input('Nenhuma atualizacao encontrada na pasta atualizacoes.\nPressione ENTER para sair.')
        return
    pkg=packages[0]
    with zipfile.ZipFile(pkg) as z:
        names=[Path(n) for n in z.namelist() if n and not n.endswith('/')]
        if not names or any(p.is_absolute() or '..' in p.parts for p in names): raise RuntimeError('Pacote invalido.')
        if not any(p.parts[0]=='app' for p in names): raise RuntimeError('Pacote sem a pasta app.')
        stamp=datetime.now().strftime('%Y%m%d_%H%M%S'); backup=BACKUPS/f'app_{stamp}'
        BACKUPS.mkdir(exist_ok=True); shutil.copytree(APP,backup)
        z.extractall(ROOT)
    requirements=ROOT/'requirements.txt'
    if requirements.exists():
        subprocess.run([sys.executable,'-m','pip','install','-r',str(requirements)],check=True)
    print(f'Atualizacao aplicada: {pkg.name}')
    print(f'Backup criado em: {backup}')
    input('Pressione ENTER para sair.')

if __name__=='__main__':
    try: main()
    except Exception as e:
        print('Falha na atualizacao:',e); input('Pressione ENTER para sair.'); sys.exit(1)
