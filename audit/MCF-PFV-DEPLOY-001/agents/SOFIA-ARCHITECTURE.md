# Sofia — Arquitetura de implantação

## Decisão

Publicar o MVP como três camadas isoladas:

1. **Interface pública:** Supabase Edge Function `predix-farmacia`.
2. **API operacional:** Supabase Edge Function `predix-api`.
3. **Persistência:** PostgreSQL Supabase em tabelas prefixadas com `pfv_`.

## Motivos

- elimina dependência de máquina local;
- mantém frontend e backend publicamente acessíveis;
- usa banco persistente;
- evita expor tabelas diretamente aos papéis públicos;
- permite testar o sistema por URL externa;
- preserva o aplicativo Python/SQLite como modo local e referência.

## Contratos

- frontend chama somente a Edge API;
- Edge API usa `service_role` interno;
- tabelas possuem RLS sem políticas públicas;
- operações de reserva e estoque usam funções transacionais;
- toda saída mantém `isDemo=true`;
- orientação clínica é encaminhada, não respondida.

## URLs

- Interface: `https://qylqyhxpwffiripcpjej.supabase.co/functions/v1/predix-farmacia`
- API: `https://qylqyhxpwffiripcpjej.supabase.co/functions/v1/predix-api`
