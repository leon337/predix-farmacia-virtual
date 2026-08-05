# Renato — Validação em navegador

## Entrada

URL Render candidata e API Supabase ativa.

## Gate implementado

Workflow: `.github/workflows/browser-render-smoke.yml`

Validações executadas:

1. HTTP 200 e `Content-Type: text/html`.
2. Health da API.
3. `status=ok`.
4. `products=500`.
5. `database=supabase-postgres`.
6. Execução do frontend em Chrome headless.
7. DOM após JavaScript contendo `PostgreSQL conectado` e `500 produtos`.
8. Ausência de `&lt;!doctype html&gt;` como conteúdo visível.
9. Screenshot móvel 390 × 844.
10. Upload obrigatório do pacote de evidências.

## Evidências

- workflow run: `31017058315`;
- job: `92343746550`;
- conclusão: `success`;
- artifact: `8934936197`;
- artifact digest: `sha256:1a83b93d909cdde81de4ddaa8753777ce2c4a573d6e31550831bfcfbb7496adb`;
- screenshot SHA-256: `762dc846922a59bdccf891fe17d98c637a34d4faf3ded51fda66aab5552d825e`;
- DOM SHA-256: `ff27800eb81602b46dead71702ee5b5a68bf92cf5edfea38fbeb4497170ce3a9`;
- health SHA-256: `a6a7eb925be2a6d6d783cd0c0acd6f860be6e21724b5a3a5bd030679d5c4510c`.

## Resultado

`PASS` — o navegador renderizou interface funcional e carregou dados do PostgreSQL.

## Handoff

Artefato entregue a Emily para inspeção independente.
