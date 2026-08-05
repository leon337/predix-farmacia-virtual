# Emily — auditoria em andamento

## Bloqueios emitidos

1. Workflow informou sucesso sem versionar arquivos novos; causa: `git diff --quiet` ignora untracked.
2. Primeira carga PostgreSQL falhou por nome globalmente único; exigido rollback e correção do modelo.
3. Primeiro smoke remoto falhou ao consultar frase com `registro`; exigida correção funcional, não redução do teste.
4. Primeiro browser gate recebeu a página anterior do cache enquanto o deploy candidato ainda compilava; a captura não foi aceita como evidência do candidato.

## Evidências já aprovadas

- hashes do espelho e catálogo;
- 500 identidades reais no PostgreSQL;
- 500 preços ausentes;
- zero disponibilidade negativa;
- API v3;
- CI local PASS;
- smoke remoto PASS;
- deploy candidato Render `live` no SHA auditado.

## Correção exigida para o navegador

- esperar o HTML público conter o marcador do candidato;
- adicionar o SHA à URL para romper cache;
- requisitar `no-cache`;
- manter todos os marcadores positivos e negativos;
- enviar screenshot, DOM, health e produto como artefato mesmo quando houver falha.

## Parecer atual

`PENDING_REPEATED_BROWSER_AND_PR_REVIEW`.

O parecer final só será emitido após screenshot e DOM do candidato, revisão do diff e checks do PR.
