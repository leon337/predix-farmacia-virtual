# Recibo final — MCF-PFV-DEPLOY-002

## Estado

`DELIVERED_AND_BROWSER_VALIDATED`

## Autoridades

- Autoridade humana final: Leandro
- Autoridade operacional: Léo
- Coordenação: Mestre

## Resultado entregue

- interface pública renderizada em HTML real;
- API Supabase operacional;
- PostgreSQL persistente com 500 produtos fictícios;
- atendimento, catálogo, reservas e relatórios disponíveis;
- endereço legado redirecionando para a interface correta;
- chave administrativa exposta invalidada;
- administração removida da superfície pública;
- validação por Chrome headless com screenshot móvel;
- execução e passagens de bastão registradas por agente.

## Endereço público

`https://predix-farmacia-virtual.onrender.com`

## Integração

- PR: `#3`
- candidato: `94de24e7e3d48e21f9c8fd26bfc43d12c8d65a3b`
- merge SHA: `9803df8400e3ff4824bc6aa4ba50a31362e134ed`
- método: squash

## Validação da main

- CI: run `31019147498` — `SUCCESS`
- Remote Deploy Smoke: run `31019147984` — `SUCCESS`
- Browser Render Smoke: run `31019147803` — `SUCCESS`

## Deploy

- Render service: `srv-d9pkpvu7bikc739i54u0`
- Render deploy: `dep-d9pl646gekts73dp0cjg`
- SHA publicado: `9803df8400e3ff4824bc6aa4ba50a31362e134ed`
- estado: `live`

## Evidência de navegador

- artifact: `8934936197`
- digest: `sha256:1a83b93d909cdde81de4ddaa8753777ce2c4a573d6e31550831bfcfbb7496adb`
- captura móvel: presente
- DOM após JavaScript: presente
- health JSON: presente
- HTML bruto visível: `false`

## Pareceres

- Emily: `PASS_WITH_RECORDED_DEVIATIONS`
- Vinícius: `PASS_WITH_RECORDED_HISTORY`
- Léo: `APPROVED`

## Desvios preservados

1. A primeira entrega pública exibiu HTML bruto.
2. O primeiro gate de smoke foi insuficiente.
3. A chave administrativa foi exposta e posteriormente invalidada.
4. Uma consulta inicial ao esquema usou coluna inexistente, sem alteração de dados.
5. O conector Render não permitiu mudar diretamente a branch configurada; a branch de publicação foi sincronizada ao SHA da main.

Nenhum desses desvios foi removido do histórico.
