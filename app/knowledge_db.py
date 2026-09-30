from __future__ import annotations
import hashlib, io, json, re, sqlite3, zipfile
from datetime import datetime
from pathlib import Path


def init(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS base_documentos(
      id INTEGER PRIMARY KEY AUTOINCREMENT, hash TEXT UNIQUE NOT NULL,
      nome TEXT NOT NULL, caminho_original TEXT, extensao TEXT, tamanho INTEGER,
      categoria TEXT, status TEXT, texto TEXT, criado_em TEXT, erro TEXT);
    CREATE TABLE IF NOT EXISTS base_relacoes(
      id INTEGER PRIMARY KEY AUTOINCREMENT, documento_id INTEGER NOT NULL,
      cargo TEXT, setor TEXT, atividade TEXT, risco_id TEXT, risco_nome TEXT,
      confianca INTEGER, aprovado INTEGER DEFAULT 0,
      UNIQUE(documento_id,cargo,setor,risco_id));
    """)


def extract_text(raw, ext):
    ext=ext.lower()
    if ext in ('.txt','.csv'): return raw.decode('utf-8','ignore')
    if ext=='.rtf': return re.sub(r'\\[a-z]+\d* ?|[{}]',' ',raw.decode('latin1','ignore'))
    if ext in ('.docx','.dotx'):
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            parts=[]
            for n in z.namelist():
                if n.startswith('word/') and n.endswith('.xml') and ('document' in n or 'header' in n or 'footer' in n):
                    xml=z.read(n).decode('utf-8','ignore'); parts.append(' '.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>',xml,re.S)))
            return re.sub(r'<[^>]+>',' ',' '.join(parts))
    if ext in ('.xlsx','.xlsm'):
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            parts=[]
            for n in z.namelist():
                if n.endswith('sharedStrings.xml') or '/worksheets/' in n:
                    parts.extend(re.findall(r'<t[^>]*>(.*?)</t>|<v[^>]*>(.*?)</v>',z.read(n).decode('utf-8','ignore'),re.S))
            return ' '.join(' '.join(x) for x in parts)
    if ext=='.pdf':
        try:
            from pypdf import PdfReader
            return '\n'.join((p.extract_text() or '') for p in PdfReader(io.BytesIO(raw)))
        except Exception as exc: raise RuntimeError('PDF sem texto extraível; use OCR ou instale pypdf.') from exc
    raise RuntimeError('Formato armazenado, mas ainda sem extrator local.')


def classify(text,name):
    t=(name+' '+text[:50000]).lower()
    tests=[('LTCAT',['ltcat','laudo técnico das condições ambientais']),('PGR',['programa de gerenciamento de riscos','inventário de riscos']),('Laudo judicial',['reclamante','reclamada','laudo técnico pericial']),('Periculosidade',['periculosidade','nr-16']),('Insalubridade',['insalubridade','nr-15']),('Ergonomia',['análise ergonômica','nr-17']),('FISPQ',['fispq','ficha de informações de segurança']),('Medição',['dosimetria','ibutg','certificado de calibração']),('EPI',['certificado de aprovação','ficha de epi'])]
    for category,words in tests:
        if any(w in t for w in words): return category
    return 'Documento SST não classificado'


def infer_field(text, labels):
    pattern=r'(?:'+('|'.join(labels))+r')\s*[:\-]\s*([^\n\r;]{2,100})'
    m=re.search(pattern,text,re.I); return re.sub(r'\s+',' ',m.group(1)).strip() if m else ''


def import_document(db_path,storage,rules_path,name,original_path,raw,persist_raw=True):
    digest=hashlib.sha256(raw).hexdigest(); ext=Path(name).suffix.lower(); storage.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        init(conn); old=conn.execute('SELECT id,nome FROM base_documentos WHERE hash=?',(digest,)).fetchone()
        if old: return {'duplicate':True,'id':old[0],'name':old[1]}
        if persist_raw:
            safe=re.sub(r'[^A-Za-z0-9._-]+','_',Path(name).name); saved=storage/f'{digest[:12]}_{safe}'; saved.write_bytes(raw)
        status='Processado'; error=''
        try: text=extract_text(raw,ext)
        except Exception as exc: text=''; status='Pendente de OCR/conversão'; error=str(exc)
        category=classify(text,name); now=datetime.now().isoformat(timespec='seconds')
        cur=conn.execute('INSERT INTO base_documentos(hash,nome,caminho_original,extensao,tamanho,categoria,status,texto,criado_em,erro) VALUES(?,?,?,?,?,?,?,?,?,?)',(digest,name,original_path,ext,len(raw),category,status,text[:2000000],now,error)); doc_id=cur.lastrowid
        cargo=infer_field(text,['cargo','função','cargo avaliado']); setor=infer_field(text,['setor','lotação'])
        if text:
            from risk_engine import suggest
            for risk in suggest({'cargo':cargo,'setor':setor,'atividades_reclamante':text[:150000]},db_path,rules_path):
                conn.execute('INSERT OR IGNORE INTO base_relacoes(documento_id,cargo,setor,atividade,risco_id,risco_nome,confianca) VALUES(?,?,?,?,?,?,?)',(doc_id,cargo,setor,'Extraída do documento',risk['id'],risk['nome'],risk['score']))
        return {'duplicate':False,'id':doc_id,'name':name,'category':category,'status':status,'relations':conn.execute('SELECT count(*) FROM base_relacoes WHERE documento_id=?',(doc_id,)).fetchone()[0]}


def overview(db_path,query=''):
    with sqlite3.connect(db_path) as conn:
        conn.row_factory=sqlite3.Row; init(conn)
        where='WHERE nome LIKE ? OR categoria LIKE ? OR texto LIKE ?' if query else ''; args=(f'%{query}%',)*3 if query else ()
        docs=[dict(x) for x in conn.execute(f'SELECT id,nome,extensao,tamanho,categoria,status,criado_em,erro FROM base_documentos {where} ORDER BY id DESC LIMIT 200',args)]
        total,size=conn.execute('SELECT count(*),coalesce(sum(tamanho),0) FROM base_documentos').fetchone(); rel=conn.execute('SELECT count(*) FROM base_relacoes').fetchone()[0]; approved=conn.execute('SELECT count(*) FROM base_relacoes WHERE aprovado=1').fetchone()[0]
        relations=[dict(x) for x in conn.execute('''SELECT r.id,r.cargo,r.setor,r.atividade,r.risco_nome,r.confianca,r.aprovado,d.nome documento_nome
          FROM base_relacoes r JOIN base_documentos d ON d.id=r.documento_id
          ORDER BY r.aprovado ASC,r.confianca DESC,r.id DESC LIMIT 200''')]
        return {'documents':docs,'relations':relations,'stats':{'documents':total,'bytes':size,'relations':rel,'approved':approved,'pending':rel-approved}}
