# Histórico de validação

## Fonte e geração

- Tentativa por API de busca: **FAIL**, HTTP 401.
- Fallback adotado: dump oficial Open Beauty Facts `en.openbeautyfacts.org.products.csv`.
- Primeira geração: **REJEITADA** por registro contaminado `pão artesanal milho`, fabricante `50g`.
- Segunda geração: **REJEITADA** após auditoria ampliada encontrar `:rest Rooibos`, Advil, antácidos e papel higiênico.
- Workflow de persistência: **FAIL** por push não fast-forward após commits paralelos; corrigido com fetch + rebase.
- Geração estrita: exigiu sinal positivo de higiene/beleza/cuidados pessoais e bloqueio de alimentos, medicamentos, bebidas e itens domésticos incompatíveis.
- Auditor independente encontrou divergências reais de pluralização e Unicode; política foi alinhada sem criar exceções individuais.
- Campo `scopeEvidence` passou a ser persistido em cada ficha.

## Artefato final

```yaml
artifact_commit: 0867042ede2f86416146854ca2cb08cf055ffbd5
catalog_sha256: 872658ab3eb807e60a03127a622ad1d2d03f5c17f58f4a04d6069ce22ab5326f
product_records: 500
distinct_barcodes: 500
products_with_images: 500
products_with_scope_evidence: 500
source_dump_bytes: 164579995
source_dump_sha256: a47ffee532c3b5a2e81944af4f2d2145e4c20d86d5f288c4f9a00d65467fc2c1
```

## PostgreSQL

Carga transacional final:

```yaml
product_records: 500
distinct_barcodes: 500
products_with_images: 500
inventory_rows: 500
simulated_stock_units: 27106
negative_availability: 0
```

## API

- `predix-api` versão de função: `4`.
- versão semântica: `1.2.0`.
- digest: `31c1b6b6536610912a4c83d3a29c7e6640635f0527c124fc1b4c5254bcba3664`.
- `catalogIdentity`: `real-with-images`.
- `productCountMeaning`: `distinct-product-records`.
- `stockCountMeaning`: `simulated-units`.

## Frontend e navegador

- Render build real inspecionado: publica somente `index.html`, `styles.css` e `app.js`.
- `startup.js` foi removido por não participar da produção.
- Cache antigo de `app.js` detectado em screenshot; corrigido com URLs versionadas.
- Primeiro browser gate após imagens: **FAIL** por falso positivo `Demo 500`, causado pelo nome da empresa seguido do contador.
- Regra corrigida para inspecionar `Demo NNN` somente nos títulos dos cards.

## Candidato final

```yaml
candidate_sha: 4436983a9054180fca7dd46e2a1534f1aab13e67
ci_run: 31054834148
ci_job: 92469963968
ci: SUCCESS
remote_smoke_run: 31054866901
remote_smoke: SUCCESS
browser_run: 31054866941
browser_job: 92470061636
browser: SUCCESS
render_deploy: dep-d9ps19bncjis73f6iorg
render_status: live
```
