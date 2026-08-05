# Histórico de validação

## Fonte e geração

- Tentativa por API de busca: **FAIL**, HTTP 401.
- Fallback adotado: dump oficial Open Beauty Facts `en.openbeautyfacts.org.products.csv`.
- Primeira geração: **REJEITADA** por registro contaminado `pão artesanal milho`, fabricante `50g`.
- Segunda geração: **REJEITADA** após auditoria ampliada encontrar `:rest Rooibos`, Advil, antácidos e papel higiênico.
- Workflow de persistência: **FAIL** por push não fast-forward após commits paralelos; corrigido com fetch + rebase.
- Geração estrita: exigiu sinal positivo de higiene, beleza ou cuidados pessoais e bloqueio de alimentos, medicamentos, bebidas e itens domésticos incompatíveis.
- Auditor independente encontrou divergências de pluralização e normalização Unicode; a política foi alinhada sem exceções individuais.
- O campo `scopeEvidence` passou a ser persistido em cada ficha.

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

Portanto, `500` representa registros distintos de produto. A quantidade de estoque é uma métrica separada: `27.106` unidades simuladas distribuídas entre os 500 produtos.

## API

- `predix-api` versão de função: `4`.
- versão semântica: `1.2.0`.
- digest: `31c1b6b6536610912a4c83d3a29c7e6640635f0527c124fc1b4c5254bcba3664`.
- `catalogIdentity`: `real-with-images`.
- `productCountMeaning`: `distinct-product-records`.
- `stockCountMeaning`: `simulated-units`.

## Frontend e navegador

- O build real do Render foi inspecionado: publica somente `index.html`, `styles.css` e `app.js`.
- `startup.js` foi removido por não participar da produção.
- Cache antigo de `app.js` foi detectado em screenshot e corrigido com URLs versionadas.
- Um browser gate confundiu o nome `Farmácia Horizonte Demo` seguido do contador `500` com produto `Demo 500`; a regra foi restringida aos títulos dos cards.
- A captura final mostra a aba Catálogo, três contadores separados, cards com fotografias e paginação.

## PR funcional #7

Head final:

```text
cb8b0461b693cb15fc83ec069121c587fa04303d
```

Checks:

```yaml
CI: 31055398649 — SUCCESS
Remote_Deploy_Smoke: 31055398764 — SUCCESS
Browser_Render_Smoke: 31055398811 — SUCCESS
```

Merge por squash:

```text
9ed6694ea599b276a6406464767ad9a7bf997bd9
```

## Bloqueio pós-merge funcional

Na primeira validação da `main` após o PR #7:

```yaml
CI: 31055528185 — SUCCESS
Remote_Deploy_Smoke: 31055530374 — SUCCESS
Browser_Render_Smoke: 31055528629 — FAIL
failed_job: 92472083071
```

Causa: a etapa do navegador ainda usava `curl` direto para `API_HEALTH` e `API_PRODUCTS`; uma leitura recebeu HTTP 500 transitório antes do Chrome. O produto, o catálogo e as imagens não foram considerados aprovados com esse resultado.

## PR corretivo #8

A correção adicionou repetição limitada somente às leituras GET, mantendo todas as asserções funcionais e visuais.

Head:

```text
3156bdef609bae749dae68e1bb4051f2157035bc
```

Checks:

```yaml
CI: 31055727024 — SUCCESS
Remote_Deploy_Smoke: 31055727021 — SUCCESS
Browser_Render_Smoke: 31055727017 — SUCCESS
Browser_job: 92472683269
```

Merge por squash:

```text
244eb25e26718ea533ea279fdd7d438a078fad6e
```

## Estado final da `main`

```yaml
final_main_sha: 244eb25e26718ea533ea279fdd7d438a078fad6e
CI: 31055829595 — SUCCESS
Remote_Deploy_Smoke: 31055829741 — SUCCESS
Browser_Render_Smoke: 31055828143 — SUCCESS
Render_deploy: dep-d9ps9449v7es73e7ahj0
Render_status: live
```

## Evidência final do navegador

```yaml
artifact_id: 8950191480
artifact_digest: sha256:d2fd52038f5419fa455cc142fdd458997c13834af1c1b17937eb0603bb495fae
screenshot_sha256: 4442f4e4a178a5564ab27f1127ad3bb979930bcad0e7abf9451e7b2e288b87fa
rendered_dom_sha256: 6f355a5bc4523bf69605562a4a29f66fc9585edb5315a1a4a18744d8e76468d9
sample_product_image_sha256: bb26489133641b49fc0144d216332d666414bbf655c05db48d0dcdb5f109d926
cards_first_page: 24
external_images_first_page: 24
fallback_errors: 0
```

Todos os bloqueios, cargas rejeitadas, falsos positivos e correções permanecem registrados.
