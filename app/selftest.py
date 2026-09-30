from __future__ import annotations

import tempfile
from pathlib import Path

import server


def main():
    server.init_db()
    dados = {
        "tipo": "Laudo judicial de insalubridade", "processo": "TESTE-INTERNO",
        "vara": "Vara de teste", "reclamante": "Parte autora de teste",
        "reclamada": "Parte ré de teste", "data": "01/01/2026",
        "local": "Local de teste", "cargo": "Função de teste", "setor": "Setor de teste",
        "objeto_pericia": "Teste técnico interno da geração documental.",
        "descricao_ambiente": "Ambiente controlado utilizado exclusivamente no autoteste.",
        "atividades_reclamante": "Atividade fictícia usada exclusivamente no autoteste.",
        "conclusao_tecnica": "O autoteste confirmou apenas o funcionamento da composição do arquivo.",
        "riscos": [{"nome": "Agente de teste", "categoria": "Teste",
                    "analise_caso": "Análise fictícia restrita ao autoteste.",
                    "conclusao_agente": "Registro fictício restrito ao autoteste."}],
        "aprovacao_tecnica": True,
    }
    with tempfile.TemporaryDirectory() as pasta:
        original = server.OUTPUTS
        server.OUTPUTS = Path(pasta)
        arquivo = server.generate_docx(dados, "teste-local")
        if not arquivo.exists() or arquivo.stat().st_size < 1000:
            raise RuntimeError("O arquivo Word de teste nao foi gerado corretamente.")
        server.OUTPUTS = original
    print("OK - banco local, dependencias e geracao de Word estao funcionando.")


if __name__ == "__main__":
    main()
