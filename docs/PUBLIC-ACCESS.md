# Acesso público — Predix Farmácia Virtual

## Endereço principal

**Interface pública:** `https://predix-farmacia-virtual.onrender.com`

## API

- Base: `https://qylqyhxpwffiripcpjej.supabase.co/functions/v1/predix-api`
- Health: `https://qylqyhxpwffiripcpjej.supabase.co/functions/v1/predix-api/api/health`

## Endereço legado

`https://qylqyhxpwffiripcpjej.supabase.co/functions/v1/predix-farmacia`

A função legada não serve mais HTML. Ela responde com redirecionamento HTTP 302 para o endereço principal.

## Infraestrutura

- frontend: Render Static Site;
- API: Supabase Edge Function;
- banco: Supabase PostgreSQL;
- catálogo: 500 produtos fictícios;
- arquivos publicados: `public/index.html`, `public/styles.css` e `public/app.js`.

## Administração

A área administrativa foi removida do frontend público. A credencial anteriormente exposta foi invalidada e nenhuma nova chave pública foi criada.

## Validação

O endereço principal é validado por Chrome headless, screenshot móvel, conferência de MIME, DOM após JavaScript e health da API. Evidências ficam em `audit/MCF-PFV-DEPLOY-002/` e no workflow `Browser Render Smoke`.

## Limites

O ambiente é exclusivamente demonstrativo. Não realiza venda, cobrança, pagamento, entrega, processamento de receita ou orientação clínica.
