import json
import sqlite3
import unicodedata
from pathlib import Path


def norm(value):
    value = unicodedata.normalize("NFKD", str(value or ""))
    return " ".join("".join(c for c in value if not unicodedata.combining(c)).lower().split())


def _history(db_path, data):
    cargo, setor, counts = norm(data.get("cargo")), norm(data.get("setor")), {}
    if not Path(db_path).exists():
        return counts
    with sqlite3.connect(db_path) as conn:
        try:
            previous_rows = conn.execute("SELECT dados_json FROM pericias").fetchall()
        except sqlite3.OperationalError:
            previous_rows = []
        for (raw,) in previous_rows:
            try: previous = json.loads(raw)
            except Exception: continue
            if not ((cargo and norm(previous.get("cargo")) == cargo) or (setor and norm(previous.get("setor")) == setor)):
                continue
            for risk in previous.get("riscos") or []:
                name = risk.get("nome") if isinstance(risk, dict) else risk
                if name: counts[norm(name)] = counts.get(norm(name), 0) + 1
        try:
            rows=conn.execute('SELECT cargo,setor,risco_nome,aprovado FROM base_relacoes').fetchall()
            wanted=set((cargo+' '+setor).split())
            for old_cargo,old_setor,risk_name,approved in rows:
                known=set(norm((old_cargo or '')+' '+(old_setor or '')).split())
                similarity=len(wanted & known)/max(1,len(wanted | known))
                if similarity>=.35 and risk_name:
                    counts[norm(risk_name)]=counts.get(norm(risk_name),0)+(2 if approved else 1)
        except sqlite3.OperationalError:
            pass
    return counts


def suggest(data, db_path, rules_path):
    base = Path(rules_path)
    rules = json.loads(base.read_text(encoding="utf-8"))
    supplemental = base.with_name("sst_catalog.json")
    if supplemental.exists():
        rules += json.loads(supplemental.read_text(encoding="utf-8"))
    history = _history(db_path, data)
    fields = {
        "cargo": norm(data.get("cargo")), "setor": norm(data.get("setor")),
        "atividades": norm(" ".join(str(data.get(k) or "") for k in ("atividades_reclamante", "atividades_reclamada", "demais_informacoes"))),
    }
    combined = " ".join(fields.values()); items = []
    for rule in rules:
        score, evidence = 0, []
        for term in rule.get("cargo_keywords", []):
            if norm(term) in fields["cargo"]: score += 28; evidence.append("Cargo: " + term)
        for term in rule.get("setor_keywords", []):
            if norm(term) in fields["setor"]: score += 22; evidence.append("Setor: " + term)
        for term in rule.get("activity_keywords", []):
            if norm(term) in combined: score += 14; evidence.append("Atividade: " + term)
        past = history.get(norm(rule["name"]), 0)
        if past: score += min(24, 8 + past * 4); evidence.append(f"{past} caso(s) local(is) semelhante(s)")
        if score < 14: continue
        score = min(score, 96)
        items.append({"id":rule["id"],"nome":rule["name"],"categoria":rule["category"],"descricao":rule["description"],
          "score":score,"confianca":"Alta" if score >= 70 else "Média" if score >= 40 else "Baixa",
          "evidencias":evidence[:8],"referencias":rule.get("references",[]),"dados_necessarios":rule.get("required_data",[]),
          "avaliacao":rule.get("assessment","Qualitativa"),"confirmado":False,
          "texto_explicativo":rule.get("explanation",rule["description"]),
          "metodologia":rule.get("methodology","Definir conforme o caso concreto e a referência aplicável."),
          "prevencao":rule.get("prevention","Verificar medidas de controle, EPCs, EPIs, treinamento e procedimentos aplicáveis."),
          "aviso":"Sugestão de triagem; não caracteriza exposição, insalubridade ou periculosidade."})
    return sorted(items, key=lambda x:(-x["score"],x["nome"]))
