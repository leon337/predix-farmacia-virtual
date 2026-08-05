# Recibo final — MCF-PFV-CATALOG-REAL-001

## Estado

`DELIVERED_REAL_CATALOG_BROWSER_VALIDATED`

## Resultado entregue

- 500 produtos para saúde com identidade regulatória real;
- nome, fabricante, detentor, processo e registro armazenados;
- 500 preços comerciais ausentes, sem valores inventados;
- estoque, clientes, reservas, pagamentos, entregas e empresa mantidos como demonstração;
- medicamentos, produtos controlados e itens invasivos/hospitalares excluídos;
- PostgreSQL, API, frontend Render e modo local usando o mesmo contrato;
- busca por nome, fabricante, categoria, SKU e registro Anvisa;
- reserva simulada sem total inventado;
- validação em Chrome headless com artefato móvel;
- falhas, rollback e correções preservados.

## Endereço público

`https://predix-farmacia-virtual.onrender.com`

## Integração

- PR funcional: `#5`
- candidato revisado: `49400af0ca1064dc7d15b8cd7cd7fef695f97c01`
- merge SHA: `f7578b0c13799c8ab7a6a873cae2ba8194e42821`
- método: squash

## Validação da main

- CI: run `31025924616` — `SUCCESS`
- Remote Deploy Smoke: run `31025924878` — `SUCCESS`
- Browser Render Smoke: run `31025926247` — `SUCCESS`
- browser artifact: `8938590089`
- artifact digest: `sha256:68dfc877f35c96f8d96b5c43d8b69e22f085a6a1472fcdfdc867fdc0ccce8e15`

## Deploy

- Render service: `srv-d9pkpvu7bikc739i54u0`
- Render deploy: `dep-d9pmcarbc2fs73dfd5ig`
- SHA publicado: `f7578b0c13799c8ab7a6a873cae2ba8194e42821`
- estado: `live`

## Dados

- produtos: `500`
- identidades reais: `500`
- preços ausentes: `500`
- estoque demonstrativo: `500` registros
- disponibilidade negativa: `0`
- catálogo SHA-256: `322a842080af74e1cafeea0a98f0ea71a930ac442eadb1d6d9911e15b9b7cf34`

## Pareceres

- Emily: `PASS_WITH_RECORDED_DEVIATIONS`
- Vinícius: `PASS_WITH_RECORDED_HISTORY`
- Léo: `APPROVED`

## Desvios preservados

1. A fonte oficial da Anvisa não respondeu ao runner dentro do timeout.
2. Um workflow declarou sucesso sem versionar arquivos novos; o gate foi corrigido.
3. A primeira carga encontrou a antiga restrição de nome globalmente único e foi revertida.
4. A identidade foi corrigida para registro + nome + fabricante.
5. O primeiro smoke por registro falhou e levou à correção da API.
6. O primeiro browser gate recebeu conteúdo antigo do cache e foi rejeitado.
7. Após o squash, a branch exclusiva do Render precisou ser reposicionada para o SHA da main.

Nenhum desses desvios foi removido do histórico.
