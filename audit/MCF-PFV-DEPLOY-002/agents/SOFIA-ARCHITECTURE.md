# Sofia — Arquitetura corretiva

## Entrada

- Evidência móvel de HTML bruto.
- Frontend anterior hospedado dentro de Supabase Edge Function.
- API e PostgreSQL funcionando.

## Análise aplicada

O defeito estava na camada de entrega do documento, não no banco. O gate anterior não distinguia corpo HTML válido de página realmente renderizada.

## Decisão

Separar responsabilidades:

```text
Render Static Site
  ├── index.html
  ├── styles.css
  └── app.js
          │ CORS/HTTPS
          ▼
Supabase Edge API
          │ service_role
          ▼
Supabase PostgreSQL
```

## Controles

- somente `public/` é publicado;
- API usa endereço absoluto;
- frontend não contém credencial administrativa;
- endereço legado redireciona ao Render;
- gate exige MIME e Chrome headless.

## Evidência

- serviço Render: `srv-d9pkpvu7bikc739i54u0`;
- URL candidata: `https://predix-farmacia-virtual.onrender.com`;
- branch: `fix/frontend-render-real-browser`.

## Resultado

`PASS` — arquitetura remove a causa do HTML bruto e mantém API/banco desacoplados.

## Handoff

Entregue a Gabriel e Laura para implementação do cliente.
