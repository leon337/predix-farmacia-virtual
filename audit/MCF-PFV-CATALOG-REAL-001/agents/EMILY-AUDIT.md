# Emily — auditoria do candidato

## Bloqueios emitidos

1. Workflow informou sucesso sem versionar arquivos novos; causa: `git diff --quiet` ignora untracked.
2. Primeira carga PostgreSQL falhou por nome globalmente único; exigido rollback e correção do modelo.
3. Primeiro smoke remoto falhou ao consultar frase com `registro`; exigida correção funcional, não redução do teste.
4. Primeiro browser gate recebeu a página anterior do cache enquanto o deploy candidato ainda compilava; a captura não foi aceita.

## Correções verificadas

- geração detecta e versiona arquivos novos;
- identidade única usa registro + nome + fabricante;
- API extrai número de registro da mensagem;
- browser gate aguarda o marcador do candidato e rompe cache por SHA;
- artefatos são enviados mesmo em falha;
- nenhum critério foi removido.

## Evidência independente

Pacote `8938372627`, digest `sha256:4d8400aa262f7a2e0a9e0346dd30398fef0948d0b85f512983455cd75318f355`.

A inspeção fora do workflow confirmou:

- screenshot móvel renderizado;
- DOM com catálogo real e 500 produtos;
- registro Anvisa e preço `Consulte o estabelecimento`;
- ausência de HTML bruto;
- ausência de nomes sintéticos;
- health com 500 identidades reais e 500 preços ausentes.

## Parecer pré-PR

`PASS_WITH_RECORDED_DEVIATIONS`.

A aprovação autoriza abertura do PR, mas não substitui a revisão de Vinícius nem o gate de Léo.
