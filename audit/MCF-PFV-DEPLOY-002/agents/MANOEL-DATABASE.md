# Manoel — Banco e persistência

## Entrada

PostgreSQL existente, catálogo com 500 produtos e credencial administrativa comprometida.

## Ações executadas

1. Tentou consultar `pfv_settings.value`; a coluna não existia.
2. Registrou a falha sem alteração de dados.
3. Inspecionou `information_schema.columns`.
4. Identificou as colunas reais: `key`, `value_hash`, `created_at`.
5. Inspecionou `pfv_update_inventory` para confirmar validação com `crypt()`.
6. Verificou após a rotação que o hash está no formato bcrypt (`$2a$`, 60 caracteres).
7. Confirmou evento de auditoria `ADMIN_KEY_ROTATED_AND_PUBLIC_ACCESS_DISABLED`.

## Evidência

- PostgreSQL: Supabase projeto `qylqyhxpwffiripcpjej`;
- catálogo: 500 produtos;
- hash administrativo: bcrypt, sem texto recuperável;
- evento registrado em `pfv_audit` em `2026-08-05 14:44:17.132019+00`.

## Resultado

`PASS_WITH_CORRECTED_QUERY` — a suposição inicial sobre o esquema falhou, foi corrigida antes de qualquer escrita e a persistência permaneceu íntegra.

## Handoff

Entregue a Ricardo para contenção de credencial e a Renato para health check remoto.
