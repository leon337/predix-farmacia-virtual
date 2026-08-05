# MCF-PFV-DEPLOY-002 — Reabertura e remediação

## Motivo da reabertura

A entrega anterior foi invalidada após evidência fornecida por Leandro mostrar que o endereço público exibia o HTML bruto como texto. O gate anterior verificava apenas a presença de palavras no corpo HTTP e não comprovava o MIME nem a renderização em navegador.

## Autoridade

- Autoridade humana final: Leandro
- Autoridade operacional: Léo
- Coordenação: Mestre
- Instrução: continuar sem interromper o fluxo até conclusão verificável.

## Objetivo corretivo

1. Publicar uma interface realmente renderizável em celular e desktop.
2. Validar `Content-Type: text/html`.
3. Executar o frontend em Chrome headless e gerar captura móvel.
4. Manter API e PostgreSQL com 500 produtos.
5. Invalidar a chave administrativa exposta.
6. Remover administração do frontend anônimo.
7. Fazer o endereço antigo redirecionar para o novo.
8. Registrar ações, evidências e handoffs dos agentes durante a execução.
9. Integrar somente após revisão, auditoria e gate operacional.

## Classificação

Classe B controlada. Ambiente integralmente fictício, sem vendas, pagamentos, entrega real, receita médica ou orientação clínica.

## Estado no momento deste artefato

`CANDIDATE_READY_FOR_REVIEW`
