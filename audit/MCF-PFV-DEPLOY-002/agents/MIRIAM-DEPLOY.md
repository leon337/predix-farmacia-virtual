# Miriam — Deploy

## Entrada

Branch `fix/frontend-render-real-browser` com três arquivos públicos isolados.

## Ações executadas

- Verificou serviços existentes no workspace Render.
- Confirmou ausência de colisão de nome.
- Criou Static Site `predix-farmacia-virtual`.
- Configurou build para copiar somente `public/index.html`, `public/styles.css` e `public/app.js` para `dist/`.
- Configurou `publishPath=dist`.
- Ativou auto-deploy na branch corretiva.
- Acompanhou o primeiro deploy até estado `live`.

## Evidências

- workspace: `tea-d2u2msje5dus73eb6ehg`;
- service: `srv-d9pkpvu7bikc739i54u0`;
- deploy: `dep-d9pkq0e7bikc739i55sg`;
- commit publicado: `43ec7b0bd602752b8bc98b29a479fe35856c539a`;
- estado: `live`;
- URL: `https://predix-farmacia-virtual.onrender.com`.

## Resultado

`PASS` — frontend servido por CDN estático com MIME apropriado e sem exposição dos demais arquivos do repositório.

## Handoff

Entregue a Renato para browser smoke e a Tiago para compatibilidade do endereço legado.
