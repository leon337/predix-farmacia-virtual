# Validação do MVP

O gate de qualidade exige:

```bash
python -m compileall -q app.py tests
python -m unittest discover -s tests -v
```

Critérios cobertos:

- seed com 500 produtos;
- empresa e produtos fictícios;
- busca, preço e estoque dinâmicos;
- política de não invenção;
- encaminhamento clínico;
- reserva atômica e idempotente;
- cancelamento e devolução de estoque;
- bloqueio de saldo negativo;
- relatórios derivados dos registros;
- interface e endpoints essenciais.
