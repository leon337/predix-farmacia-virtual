# API do MVP

Todas as respostas operacionais incluem indicação de ambiente demonstrativo quando aplicável.

- `GET /api/health`: saúde e quantidade de produtos.
- `GET /api/company`: dados da empresa fictícia.
- `GET /api/products?query=&page=&pageSize=`: catálogo paginado.
- `POST /api/chat`: mensagem e `sessionId`; devolve intenção, ferramenta, fontes e encaminhamento.
- `POST /api/reservations`: exige `Idempotency-Key` e itens.
- `GET /api/reservations/{id}`: consulta da reserva.
- `POST /api/reservations/{id}/cancel`: cancelamento transacional.
- `GET /api/reports`: indicadores básicos.
- `POST /api/admin/inventory/{productId}`: exige `X-Admin-Key`.
