# Ricardo — Segurança e permissões

## Controles aplicados

- RLS habilitado em todas as tabelas `pfv_*`.
- Nenhuma política para `anon` ou `authenticated`: acesso direto negado por padrão.
- A Edge API opera com `service_role` interno.
- Chave administrativa armazenada somente como hash bcrypt.
- CORS limitado aos cabeçalhos e métodos necessários.
- CSP, `nosniff`, `no-referrer` e bloqueio de frames na interface.
- Sem dados pessoais reais, pagamentos, receitas ou orientação clínica.

## Achado e correção

O advisor Supabase detectou que funções `SECURITY DEFINER` herdavam `EXECUTE` do papel `PUBLIC`. O gate foi bloqueado.

Migration corretiva: `harden_predix_rpc_permissions`.

Ação:

```sql
revoke execute ... from public, anon, authenticated;
grant execute ... to service_role;
```

## Revalidação

Após a correção, desapareceram os avisos de execução pública das três RPCs. Permanecem apenas:

- informações de RLS sem política, comportamento intencional de negação total;
- aviso de proteção contra senhas vazadas do módulo Auth compartilhado, não utilizado por este MVP.

## Resultado

Gate de segurança do escopo Predix: `PASS`.
