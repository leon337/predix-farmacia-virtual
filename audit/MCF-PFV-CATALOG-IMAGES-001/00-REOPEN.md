# Reabertura — MCF-PFV-CATALOG-IMAGES-001

## Motivo

A missão foi reaberta após a constatação de que o site público não exibia imagens nos cards e não comunicava com clareza a diferença entre produtos cadastrados e unidades de estoque.

## Requisito corrigido

- exatamente 500 registros distintos de produtos;
- exatamente 500 códigos de barras distintos;
- exatamente 500 fotografias de produto verificadas;
- estoque contabilizado separadamente como unidades simuladas;
- imagens inseridas no site real, não em mockup ou imagem gerada;
- catálogo limitado a higiene, beleza e cuidados pessoais;
- alimentos, medicamentos, bebidas e itens domésticos incompatíveis excluídos;
- validação em navegador real antes de merge.

## Auditoria inicial do banco

```yaml
product_records: 500
distinct_product_identities: 500
inventory_rows: 500
stock_units_before_image_catalog: 31030
image_column_before_migration: false
```

A contagem de 500 já representava linhas de produtos. O defeito era ausência de imagens, ambiguidade visual e falta de separação explícita entre quantidade de produtos e unidades de estoque.
