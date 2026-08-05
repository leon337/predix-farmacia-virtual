# Manoel — dados e banco

## Artefatos

- `scripts/build_real_catalog.py`
- `data/real_products.json`
- `SOURCE-REPORT.md`
- migrações em `supabase/migrations/`

## Controles

- hash do espelho e do catálogo;
- exatamente 500 registros;
- identidade única por registro, nome e fabricante;
- preço nulo;
- ausência de substância ativa;
- classe I ou II;
- carga por tabela temporária e transação;
- validação pós-carga;
- evento `REAL_CATALOG_REPLACED`.

## Falha preservada

A primeira carga encontrou nomes comerciais repetidos. A transação foi revertida. A restrição antiga de nome único foi substituída por identidade regulatória.
