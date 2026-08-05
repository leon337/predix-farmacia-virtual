# Sofia — arquitetura

## Decisão

Separar três conceitos no modelo e na API:

```text
identity_real = true
operations_simulated = true
price_cents = null
```

## Fluxo

```text
base regulatória
→ importador determinístico
→ JSON versionado e hashado
→ staging PostgreSQL
→ validação transacional
→ produtos reais + estoque demonstrativo
→ Edge API
→ frontend Render
```

A API foi atualizada antes da carga para evitar janela com `R$ 0,00`. O modo local passou a ler o mesmo JSON.
