# Ricardo — Segurança

## Entrada

A chave administrativa havia sido publicada na conversa e precisava ser tratada como comprometida.

## Ações executadas

- Classificou a credencial como comprometida.
- Substituiu `pfv_settings.value_hash` pelo hash bcrypt de um valor aleatório irrecuperável.
- Inseriu evento de auditoria no PostgreSQL.
- Removeu a administração do frontend público.
- Manteve as tabelas `pfv_*` sob RLS.
- Manteve RPCs transacionais restritas ao `service_role`.
- Não gerou nem exibiu nova senha administrativa.

## Evidências

- evento: `ADMIN_KEY_ROTATED_AND_PUBLIC_ACCESS_DISABLED`;
- recurso: `pfv_settings/admin_key`;
- hash atual: prefixo `$2a$`, comprimento 60;
- `public/index.html` não contém campo de chave nem formulário de estoque.

## Resultado

`PASS` — a credencial exposta foi invalidada e a superfície administrativa anônima foi removida.

## Restrição assumida

Atualizações de estoque deixam de ser função pública do MVP. Manutenção administrativa exige canal autenticado a ser desenvolvido em fase posterior.

## Handoff

Entregue a Miriam para publicação e a Emily para auditoria de exposição.
