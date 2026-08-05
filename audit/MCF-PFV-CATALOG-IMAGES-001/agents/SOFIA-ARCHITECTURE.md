# Sofia — arquitetura

## Entrada

Site sem fotografias, contagem visual ambígua e base regulatória sem imagem confiável para todas as fichas.

## Decisão

Separar:

- identidade varejista real: GTIN + nome + marca + imagem + fonte;
- operação simulada: empresa, estoque, reservas, pagamentos e entregas;
- contagem de catálogo: registros distintos;
- contagem de estoque: unidades simuladas.

## Contrato final

```text
500 product records
500 distinct barcodes
500 verified product images
27106 simulated stock units
```

## Handoff

Entregue a Manoel para modelo e carga; a Tiago para API; a Gabriel e Laura para frontend.
