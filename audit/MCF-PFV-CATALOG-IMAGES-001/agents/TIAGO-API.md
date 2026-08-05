# Tiago — API

## Entrega

`predix-api` v4 / `1.2.0`.

Novos campos públicos:

- `barcode`;
- `imageUrl`;
- `imageSource`;
- `imageVerifiedAt`;
- `sourceDataset`;
- `identitySource`;
- `stockIsSimulated`.

Novas métricas:

- `productRecords`;
- `distinctProducts`;
- `productsWithImages`;
- `productsWithBarcode`;
- `stockUnitsSimulated`.

## Resultado

```yaml
function_version: 4
semantic_version: 1.2.0
digest: 31c1b6b6536610912a4c83d3a29c7e6640635f0527c124fc1b4c5254bcba3664
catalogIdentity: real-with-images
productCountMeaning: distinct-product-records
stockCountMeaning: simulated-units
```
