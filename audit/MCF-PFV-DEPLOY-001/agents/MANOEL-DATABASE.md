# Manoel — Banco de dados e integridade

## Entrega

Migration aplicada: `create_predix_farmacia_virtual_mvp`.

## Estruturas

- `pfv_company`
- `pfv_products`
- `pfv_inventory`
- `pfv_customers`
- `pfv_reservations`
- `pfv_reservation_items`
- `pfv_conversations`
- `pfv_product_queries`
- `pfv_audit`
- `pfv_settings`

## Funções transacionais

- `pfv_create_reservation`
- `pfv_cancel_reservation`
- `pfv_update_inventory`

## Controles

- chaves estrangeiras;
- SKUs e nomes únicos;
- preço positivo;
- estoque total e reservado não negativos;
- reserva nunca superior ao total;
- idempotência por chave única;
- atualização com lock transacional;
- chave administrativa armazenada somente como hash bcrypt;
- auditoria de reserva, cancelamento e estoque.

## Prova

Consulta pós-migração:

```json
{
  "products": 500,
  "inventory_rows": 500,
  "companies": 1,
  "minimum_available": 0,
  "demo_products": 500
}
```

Não foram utilizados dados comerciais ou pessoais reais.
