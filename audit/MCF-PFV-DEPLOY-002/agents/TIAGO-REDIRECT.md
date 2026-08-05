# Tiago — Compatibilidade e redirecionamento

## Entrada

O endereço legado da Supabase Edge Function havia exibido HTML bruto e já tinha sido compartilhado.

## Ações executadas

- Substituiu o conteúdo da função `predix-farmacia` por redirecionamento HTTP 302.
- Permitiu somente `GET` e `HEAD`.
- Adicionou `Cache-Control: no-store` e `X-Content-Type-Options: nosniff`.
- Definiu o destino como o Static Site Render.

## Evidências

- Edge Function: `predix-farmacia`;
- versão: `2`;
- status: `ACTIVE`;
- digest: `491ee04756da230c2e296c564ddee2f0dbb7e6776bafb06fda48874a05105e31`;
- destino: `https://predix-farmacia-virtual.onrender.com`.

## Resultado

`PASS` — o endereço anteriormente distribuído deixa de servir o documento defeituoso e encaminha ao frontend correto.

## Handoff

Entregue a Renato para inclusão no smoke final e a Emily para auditoria do caminho legado.
