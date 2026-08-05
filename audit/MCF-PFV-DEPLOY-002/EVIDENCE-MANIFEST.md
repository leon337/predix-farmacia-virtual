# Manifesto de evidências — MCF-PFV-DEPLOY-002

## Falha que originou a remediação

O endereço público anterior exibiu HTML bruto no navegador móvel. Essa falha permanece registrada e não é anulada pela correção posterior.

## Evidência independente de navegador

- workflow: `Browser Render Smoke`
- run inicial auditado: `31017058315`
- job: `92343746550`
- artifact: `8934936197`
- artifact digest: `sha256:1a83b93d909cdde81de4ddaa8753777ce2c4a573d6e31550831bfcfbb7496adb`

### Conteúdo descompactado e verificado

```text
762dc846922a59bdccf891fe17d98c637a34d4faf3ded51fda66aab5552d825e  predix-mobile.png
ff27800eb81602b46dead71702ee5b5a68bf92cf5edfea38fbeb4497170ce3a9  rendered.html
a6a7eb925be2a6d6d783cd0c0acd6f860be6e21724b5a3a5bd030679d5c4510c  health.json
```

## Pull request e integração

- PR corretivo: `#3`
- candidato revisado: `94de24e7e3d48e21f9c8fd26bfc43d12c8d65a3b`
- merge por squash: `9803df8400e3ff4824bc6aa4ba50a31362e134ed`
- revisão Vinícius: `PASS_WITH_RECORDED_HISTORY`
- auditoria Emily: `PASS_WITH_RECORDED_DEVIATIONS`
- gate Léo: `APPROVED`

## Validação da `main`

```text
CI                      run 31019147498  SUCCESS
Remote Deploy Smoke     run 31019147984  SUCCESS
Browser Render Smoke    run 31019147803  SUCCESS
```

O browser smoke da `main` validou MIME HTML, redirecionamento legado, health do PostgreSQL, execução JavaScript, catálogo de 500 produtos, captura móvel e ausência de HTML bruto visível.

## Infraestrutura final

- Render service: `srv-d9pkpvu7bikc739i54u0`
- Render deploy: `dep-d9pl646gekts73dp0cjg`
- Render deployed SHA: `9803df8400e3ff4824bc6aa4ba50a31362e134ed`
- Render status: `live`
- Render URL: `https://predix-farmacia-virtual.onrender.com`
- Supabase project: `qylqyhxpwffiripcpjej`
- API function: `predix-api`
- Legacy redirect function: `predix-farmacia`, version `2`
- Legacy function digest: `491ee04756da230c2e296c564ddee2f0dbb7e6776bafb06fda48874a05105e31`

## Segurança final

- chave administrativa anteriormente exposta: invalidada;
- nova chave administrativa pública: não criada;
- painel administrativo público: removido;
- tabelas `pfv_*`: RLS habilitado;
- RPCs transacionais: execução pública revogada;
- catálogo: 500 registros fictícios persistentes.

## Desvio de configuração do Render

O conector disponível não expõe alteração da branch configurada em um serviço existente. Para preservar a URL, a branch observada pelo Render foi sincronizada ao merge SHA da `main`. O deploy final comprova que o serviço publicou exatamente `9803df8400e3ff4824bc6aa4ba50a31362e134ed`.

## Veredito

`DELIVERED_AND_BROWSER_VALIDATED`
