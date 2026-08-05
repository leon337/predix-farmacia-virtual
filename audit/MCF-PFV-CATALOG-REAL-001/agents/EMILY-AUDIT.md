# Emily — auditoria em andamento

## Bloqueios emitidos

1. Workflow informou sucesso sem versionar arquivos novos; causa: `git diff --quiet` ignora untracked.
2. Primeira carga PostgreSQL falhou por nome globalmente único; exigido rollback e correção do modelo.
3. Primeiro smoke remoto falhou ao consultar frase com `registro`; exigida correção funcional, não redução do teste.

## Evidências já aprovadas

- hashes do espelho e catálogo;
- 500 identidades reais no PostgreSQL;
- 500 preços ausentes;
- zero disponibilidade negativa;
- API v3;
- CI local PASS;
- smoke remoto PASS.

## Parecer atual

`PENDING_BROWSER_AND_PR_REVIEW`.

O parecer final só será emitido após screenshot/DOM do Render, revisão do diff e checks do PR.
