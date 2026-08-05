# Emily — auditoria do candidato

## Bloqueios emitidos

1. Produto `pão artesanal milho`, fabricante `50g`.
2. Itens fora do escopo: `:rest Rooibos`, Advil, antácidos e papel higiênico.
3. Catálogo sem evidência de escopo persistida.
4. Render carregando JavaScript antigo do cache.
5. Gate confundindo `Farmácia Horizonte Demo` + contador `500` com produto `Demo 500`.

## Evidências aprovadas

- 500 registros distintos;
- 500 códigos de barras;
- 500 imagens verificadas;
- 500 evidências de escopo;
- zero termo bloqueado na consulta pós-carga;
- 27.106 unidades simuladas separadas;
- API v4;
- CI, smoke remoto e browser smoke aprovados;
- pacote visual aberto fora do workflow;
- 24 cards, 24 imagens externas e zero fallback no primeiro lote.

## Parecer pré-PR

`PASS_WITH_RECORDED_DEVIATIONS`.

O merge permanece condicionado à revisão de Vinícius, aos três checks do PR e ao gate de Léo.
