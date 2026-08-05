# Recibo final — MCF-PFV-CATALOG-IMAGES-001

## Estado

`DELIVERED_500_DISTINCT_PRODUCTS_WITH_IMAGES_BROWSER_VALIDATED`

## Endereço público

`https://predix-farmacia-virtual.onrender.com`

## Resultado entregue

- 500 registros distintos de produtos;
- 500 códigos de barras distintos;
- 500 fotografias de produtos verificadas;
- 500 evidências de escopo persistidas;
- primeira página com 24 cards e 24 imagens externas;
- paginação `Produtos 1–24 de 500`;
- 27.106 unidades simuladas de estoque, contabilizadas separadamente;
- preços comerciais ausentes, sem valores inventados;
- catálogo limitado a higiene, beleza e cuidados pessoais;
- alimentos, medicamentos, bebidas e itens domésticos incompatíveis excluídos;
- empresa, estoque, reservas, pagamentos e entregas mantidos como demonstração.

## Catálogo

```yaml
artifact_commit: 0867042ede2f86416146854ca2cb08cf055ffbd5
catalog_sha256: 872658ab3eb807e60a03127a622ad1d2d03f5c17f58f4a04d6069ce22ab5326f
product_records: 500
distinct_barcodes: 500
products_with_images: 500
products_with_scope_evidence: 500
prices_provided: 0
blocked_categories_present: 0
```

## PostgreSQL

```yaml
product_records: 500
inventory_rows: 500
simulated_stock_units: 27106
negative_availability: 0
```

`500` é a quantidade de produtos cadastrados. `27.106` é a soma das unidades simuladas distribuídas entre esses produtos.

## API

```yaml
function: predix-api
function_version: 4
semantic_version: 1.2.0
digest: 31c1b6b6536610912a4c83d3a29c7e6640635f0527c124fc1b4c5254bcba3664
catalogIdentity: real-with-images
productCountMeaning: distinct-product-records
stockCountMeaning: simulated-units
```

## Integração funcional

- PR funcional: `#7`;
- head final do PR: `cb8b0461b693cb15fc83ec069121c587fa04303d`;
- merge funcional: `9ed6694ea599b276a6406464767ad9a7bf997bd9`;
- método: squash.

Checks do PR #7:

```yaml
CI: 31055398649 — SUCCESS
Remote_Deploy_Smoke: 31055398764 — SUCCESS
Browser_Render_Smoke: 31055398811 — SUCCESS
```

## Desvio pós-merge funcional

A primeira validação do browser na `main` falhou antes do Chrome por HTTP 500 transitório na leitura do health:

```yaml
failed_run: 31055528629
failed_job: 92472083071
CI_same_sha: 31055528185 — SUCCESS
Remote_smoke_same_sha: 31055530374 — SUCCESS
```

Esse resultado bloqueou o fechamento.

## Integração corretiva

- PR corretivo: `#8`;
- head: `3156bdef609bae749dae68e1bb4051f2157035bc`;
- merge corretivo e SHA final funcional: `244eb25e26718ea533ea279fdd7d438a078fad6e`;
- alteração: repetição limitada somente às leituras GET do browser gate;
- critérios funcionais e visuais preservados.

Checks do PR #8:

```yaml
CI: 31055727024 — SUCCESS
Remote_Deploy_Smoke: 31055727021 — SUCCESS
Browser_Render_Smoke: 31055727017 — SUCCESS
Browser_job: 92472683269
```

## Validação final da `main`

```yaml
final_main_sha: 244eb25e26718ea533ea279fdd7d438a078fad6e
CI: 31055829595 — SUCCESS
Remote_Deploy_Smoke: 31055829741 — SUCCESS
Browser_Render_Smoke: 31055828143 — SUCCESS
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

## Produção

```yaml
render_service: srv-d9pkpvu7bikc739i54u0
render_deploy: dep-d9ps9449v7es73e7ahj0
sha_publicado: 244eb25e26718ea533ea279fdd7d438a078fad6e
status: live
```

## Pareceres

- Emily: `PASS_WITH_RECORDED_DEVIATIONS`;
- Vinícius: `PASS_WITH_RECORDED_HISTORY`;
- Léo: `APPROVED`.

## Desvios preservados

1. Geração de imagem em vez de alteração do site na tentativa anterior.
2. HTTP 401 na estratégia inicial de busca.
3. Catálogo rejeitado por produto alimentar e fabricante inválido.
4. Catálogo rejeitado por itens fora do escopo, incluindo bebida, medicamentos e produto doméstico.
5. Push automático não fast-forward.
6. Dependência em arquivo não publicado pelo build do Render.
7. JavaScript antigo servido por cache.
8. Falsos positivos de pluralização, Unicode e `Demo 500` nos gates.
9. HTTP 500 transitório no smoke remoto do primeiro head do PR funcional.
10. Browser Render Smoke da primeira `main` funcional bloqueado por leitura GET transitória.

Nenhum desses desvios foi apagado pelo fechamento.
