# Reabertura — MCF-PFV-CATALOG-REAL-001

## Motivo

A entrega anterior usava 500 produtos sintéticos. Leandro corrigiu o requisito: os produtos deveriam possuir identidade real.

## Objetivo corrigido

- 500 produtos para saúde com nome, fabricante e registro reais;
- estoque, clientes, reservas, pagamentos e entregas simulados;
- preços comerciais não inventados;
- exclusão de medicamentos, produtos controlados e itens invasivos ou hospitalares;
- banco PostgreSQL, API, frontend, modo local e testes coerentes;
- execução visível, falhas preservadas e artefatos auditáveis.

## Estado inicial

- produtos sintéticos: 500;
- preços fictícios: 500;
- registros Anvisa: 0;
- frontend declarava catálogo sintético;
- testes exigiam nomes Demo.

A missão foi reaberta sem apagar a trilha anterior `MCF-PFV-DEPLOY-002`.
