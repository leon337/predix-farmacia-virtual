# Renato — validação

## Gates criados ou reforçados

- geração com 500 produtos, GTINs e imagens;
- auditor independente do catálogo;
- CI de Python, JavaScript, frontend e modo local;
- smoke remoto com download real da fotografia;
- consulta por código de barras;
- reserva criada e cancelada;
- relatório com produtos e unidades separados;
- Chrome headless com 24 cards, 24 imagens e screenshot móvel.

## Candidato final

```yaml
ci_run: 31054834148
ci_job: 92469963968
ci: SUCCESS
remote_smoke_run: 31054866901
remote_smoke: SUCCESS
browser_run: 31054866941
browser_job: 92470061636
browser: SUCCESS
```

## Falhas preservadas

- HTTP 401 na estratégia inicial de API;
- push não-fast-forward do bot;
- cache do JavaScript antigo;
- falsos positivos de plural, Unicode e `Demo 500`;
- estados transitórios HTTP durante cargas.
