# Histórico de validação

## Fonte e geração

- Fonte oficial tentada: `TA_PRODUTO_SAUDE_SITE.csv` da Anvisa.
- Run `31021991343`, job `92360756428`: **FAIL**, timeout de rede antes do parser.
- Run `31022407792`, job `92362209774`: diagnóstico deliberado; estrutura e hash do espelho confirmados.
- SHA-256 do espelho: `d20df633de53a2c79a2efa03ebae61db72fcb7e27941f23993784f179130f173`.
- Run `31022641294`, job `92363009752`: validações passaram, porém Emily identificou falso positivo; arquivos novos não foram versionados.
- Correção: `git status --porcelain` no lugar de `git diff --quiet`.
- Run `31022791987`, job `92363525937`: **PASS**, catálogo e relatório persistidos.
- Commit de dados: `be76a92a585158ad0a7a6b91d25b3aee65fa4230`.
- SHA-256 do catálogo: `322a842080af74e1cafeea0a98f0ea71a930ac442eadb1d6d9911e15b9b7cf34`.

## Banco PostgreSQL

Pré-carga validada pelo próprio banco: HTTP 200, 421.854 bytes, 500 produtos e hash exato.

Primeira carga: **FAIL** por nome comercial repetido sob a restrição antiga `pfv_products_name_key`. Rollback comprovado: 500 produtos sintéticos, 0 identidades reais.

Correção: remoção da unicidade global de nome e preservação do índice único por `anvisa_registration + name + manufacturer`.

Segunda carga: **PASS**.

```yaml
products: 500
realIdentities: 500
pricesMissing: 500
inventory: 500
negativeAvailability: 0
replacementAuditEvents: 1
```

## API

- `predix-api` v2: preço nulo e identidade real.
- Pré-carga: `catalogIdentity=transition`, comprovando ordem correta.
- Pós-carga: `catalogIdentity=real`, 500 identidades reais e 500 preços ausentes.
- Primeiro smoke remoto `31024349539`, job `92368837338`: **FAIL**; busca por frase com a palavra `registro` não localizou o número.
- `predix-api` v3, digest `54801b70043a895976f7bce0ef1b6a446d8dc5635c23946995d8e4ffb28a3c66`: extrai número regulatório.
- Reexecução do mesmo run, job `92369694281`: **PASS**.

## Modo local

- CI `31024347215`, job `92368829741`: **PASS**.
- Compile, hash, estrutura, 12 testes e smoke HTTP: PASS.

## Pendente neste checkpoint

- deploy Render do frontend candidato;
- Browser Render Smoke e screenshot móvel;
- PR, revisão, gate de Léo e merge;
- checks e deploy do SHA final da main.
