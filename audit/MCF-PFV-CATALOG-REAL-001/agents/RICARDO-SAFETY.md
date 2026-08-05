# Ricardo — segurança

## Limites aplicados

- sem medicamentos;
- sem produtos controlados;
- sem itens invasivos ou de uso hospitalar;
- sem substância ativa, dose, diagnóstico ou tratamento;
- sem preço inventado;
- sem links de compra;
- sem área administrativa pública.

## Banco

- RLS preservado;
- funções de carga e reserva restritas ao `service_role`;
- carga fixada em URL de commit e hashes exatos;
- rollback verificado após falha;
- fonte externa não controla comandos ou SQL.
