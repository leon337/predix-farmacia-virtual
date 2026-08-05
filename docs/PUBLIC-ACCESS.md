# Acesso público — Predix Farmácia Virtual

## Sistema

- Interface pública: `https://qylqyhxpwffiripcpjej.supabase.co/functions/v1/predix-farmacia`
- API pública controlada: `https://qylqyhxpwffiripcpjej.supabase.co/functions/v1/predix-api`
- Health check: `https://qylqyhxpwffiripcpjej.supabase.co/functions/v1/predix-api/api/health`

## Infraestrutura

- Frontend: Supabase Edge Function `predix-farmacia`
- API: Supabase Edge Function `predix-api`
- Banco: Supabase PostgreSQL, tabelas prefixadas com `pfv_`
- Catálogo: 500 produtos fictícios

## Limites

O ambiente é exclusivamente demonstrativo. Não realiza venda, pagamento, entrega, processamento de receita ou orientação clínica.

## Administração

A atualização de estoque exige a chave administrativa entregue diretamente à autoridade humana final. A chave não é versionada no repositório.
