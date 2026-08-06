# Validação — MCF-PFV-SAFE-LAYOUT-001

## Escopo

- catálogo público não medicamentoso;
- imagens em moldura fixa;
- conteúdo abaixo da imagem, sem sobreposição;
- reserva e atendimento conversacional removidos da interface;
- funções de reserva bloqueadas no PostgreSQL;
- nenhum produto ou estoque alterado nesta missão.

## Candidato

```yaml
branch: feat/medicamentos-imagens-oficiais-layout
candidate_sha: 67b1fbeab9f2942ac36e2cd7b4979f1d76f119b0
render_service: srv-d9pkpvu7bikc739i54u0
render_deploy: dep-d9qfs8btqb8s73aucor0
render_status: live
url: https://predix-farmacia-virtual.onrender.com
```

## Validação HTTP direta

```yaml
html_status: 200
html_content_type: text/html; charset=utf-8
safe_marker: true
asset_version: layout-safe-20260806-2
reservation_tab_absent: true
chat_form_absent: true

css_status: 200
css_content_type: text/css; charset=utf-8
fixed_image_row: true
object_fit_contain: true
separate_card_body: true

javascript_status: 200
javascript_content_type: application/javascript
image_wrapper_present: true
structured_details_present: true
reservation_api_reference_absent: true
reservation_button_absent: true
```

## API e banco

```yaml
api_health_status: 200
products: 500
products_with_images: 500
first_page_items: 24
simulated_stock_units: 27106
reservation_function_block_message: present
anon_create_reservation: false
authenticated_create_reservation: false
service_role_execute_retained: true
```

## Arquivos do PR #10

- `.github/workflows/browser-render-smoke.yml`
- `.github/workflows/ci.yml`
- `.github/workflows/remote-deploy-smoke.yml`
- `public/app.js`
- `public/index.html`
- `public/styles.css`
- `supabase/migrations/20260806183000_disable_public_reservations.sql`

## Limitação registrada

O GitHub Actions não criou `workflow_runs` ou `check_runs` para a branch/PR durante esta execução. A consulta de permissões do Actions retornou `403 Resource not accessible by integration`.

Por esse motivo, não existe declaração de CI `PASS` nesta fase. A validação foi feita diretamente contra o deploy Render e o PostgreSQL/Supabase, e esta limitação permanece registrada.

## Parecer

`PASS_WITH_ACTIONS_CONNECTOR_LIMITATION`
