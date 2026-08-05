# Passagens de bastão

1. **Mestre → Manoel:** auditar banco e separar contagem de produtos da soma de estoque.
2. **Manoel → Sofia:** entregar esquema real e ausência de campos de imagem.
3. **Sofia → Gabriel/Manoel:** definir catálogo varejista com GTIN, imagem e operação simulada separada.
4. **Gabriel → Renato:** entregar importador e workflow para geração auditável.
5. **Renato → Emily:** entregar catálogo gerado para amostragem independente antes da carga.
6. **Emily → Manoel:** bloquear catálogos contaminados e exigir filtros de escopo.
7. **Manoel → Tiago:** entregar estrutura PostgreSQL e contrato de dados para API v4.
8. **Tiago → Gabriel/Laura:** expor `barcode`, `imageUrl` e métricas separadas para o frontend.
9. **Gabriel → Laura:** entregar cards com tag `<img>`, GTIN e quantidade simulada separada.
10. **Laura → Miriam:** entregar layout responsivo e dependências estáticas reais do Render.
11. **Miriam → Renato:** entregar URL candidata e SHA publicado.
12. **Renato → Emily:** entregar CI, smoke remoto, DOM, screenshot e imagem binária.
13. **Emily → Vinícius:** candidato liberado para revisão somente após pacote visual final.
14. **Vinícius → Léo:** PR revisado e checks aprovados.
15. **Léo → Mestre:** autorização de integração condicionada aos gates da `main`.

Cada passagem está associada a commits, runs, deploys ou consultas registradas na trilha desta missão.
