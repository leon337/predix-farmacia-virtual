# MCF-PFV-DEPLOY-001 — Contrato da missão

## Autoridade

- Autoridade humana final: Leandro
- Autoridade operacional: Léo
- Coordenação: Mestre
- Autorização: execução completa, incluindo banco, publicação, testes, correções e integração.

## Objetivo

Entregar a Predix Farmácia Virtual em endereço público, com banco persistente, API operacional, interface funcional, validação remota, segurança mínima, rastreabilidade, artefatos de agentes e fechamento auditável.

## Critérios de conclusão

1. URL pública responde HTTP 200.
2. API informa `status=ok`.
3. PostgreSQL contém exatamente 500 produtos fictícios.
4. Catálogo, conversa, reserva e relatórios funcionam remotamente.
5. Tabelas não são acessíveis pelos papéis `anon` e `authenticated`.
6. Funções `SECURITY DEFINER` são executáveis somente por `service_role`.
7. GitHub Actions produz prova independente do smoke remoto.
8. Agentes selecionados registram entregas e passagens de bastão.
9. PR é revisado e integrado à `main`.

## Classificação

Classe B controlada: dados integralmente fictícios, sem venda, pagamento, receita médica, entrega real ou orientação clínica.
