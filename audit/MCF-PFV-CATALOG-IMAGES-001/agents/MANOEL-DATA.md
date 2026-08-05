# Manoel — dados e PostgreSQL

## Ações

- auditou o modelo existente;
- adicionou campos de código de barras e imagem;
- criou índice único parcial de GTIN;
- criou função transacional `pfv_replace_retail_catalog_from_json`;
- implementou validações de 500 registros, 500 barcodes, 500 imagens e preço nulo;
- executou cargas somente após validação de HTTP, tamanho, hash e metadados;
- manteve rollback integral em caso de falha;
- alinhou banco ao artefato final fixado.

## Resultado

```yaml
product_records: 500
distinct_barcodes: 500
products_with_images: 500
inventory_rows: 500
simulated_stock_units: 27106
negative_availability: 0
catalog_sha256: 872658ab3eb807e60a03127a622ad1d2d03f5c17f58f4a04d6069ce22ab5326f
```
