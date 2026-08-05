# Estoque

- Versão: 1.0.0
- Estado: ativo
- Tipo de conhecimento: procedimento permanente

Disponível = quantidade total - quantidade reservada.

Toda consulta deve usar a fonte dinâmica. Reservas não podem exceder o disponível, atualizações não podem produzir saldo negativo e alterações devem ser auditadas. Cancelar uma reserva ativa devolve a quantidade reservada.
