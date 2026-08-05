# Gabriel — frontend

## Entrega real no site

- criou `<img>` por card usando `imageUrl` da API;
- adicionou GTIN, marca, apresentação e fonte da fotografia;
- exibiu posição `Produto N de 500`;
- separou quantidade disponível em `unidades simuladas`;
- adicionou paginação `Produtos 1–24 de 500`;
- adicionou fallback explícito sem representar imagem genérica como foto real;
- tornou a aba Catálogo a tela inicial;
- removeu `startup.js`, que não participava do build real;
- invalidou cache de CSS e JavaScript com URLs versionadas.

## Falha corrigida

O Render serviu `index.html` novo com `app.js` antigo em cache. A captura exibiu cards sem `<img>`. A versão dos assets corrigiu o defeito e o browser gate posterior comprovou 24 imagens no primeiro lote.
