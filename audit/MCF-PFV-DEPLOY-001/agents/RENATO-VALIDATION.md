# Renato — Validação remota

## Workflow

- Nome: `Remote Deploy Smoke`
- Arquivo: `.github/workflows/remote-deploy-smoke.yml`
- Run: `31013163332`
- Job: `92330304228`
- Resultado: `SUCCESS`

## Testes executados contra a internet

1. Interface pública responde HTTP 200.
2. HTML contém `Predix Farmácia Virtual` e `AMBIENTE FICTÍCIO`.
3. Health retorna `status=ok`.
4. Banco identificado como `supabase-postgres`.
5. Catálogo retorna exatamente 500 produtos.
6. Empresa retorna `isDemo=true`.
7. Chat consulta `search_products` e devolve fontes.
8. Reserva remota é criada com HTTP 201.
9. Relatórios refletem atendimento e reserva.

## Recibo do job

```json
{
  "frontend": "PASS",
  "health": {
    "status": "ok",
    "products": 500,
    "database": "supabase-postgres",
    "version": "1.0.0",
    "isDemo": true
  },
  "company": "Farmácia Horizonte Demo",
  "catalog_total": 500,
  "chat": "PASS",
  "reservation": "3a94034e-b5c8-4b6e-b04b-505152e97a4a",
  "reports": "PASS"
}
```

## Resultado

Gate funcional remoto: `PASS`.
