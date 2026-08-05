# Renato — validação

## Gates executados

- ingestão oficial: falhou por timeout, sem alteração;
- diagnóstico do espelho: estrutura e hash confirmados;
- geração: validação passou, mas artefatos não foram versionados;
- gate corrigido: artefatos persistidos;
- CI local: PASS;
- smoke remoto inicial: FAIL por busca de registro;
- mesma execução após API v3: PASS.

## Gates atualizados

- CI exige 500 identidades reais, registro e preço nulo;
- smoke remoto cria e cancela reserva;
- browser smoke exige textos reais, DOM, screenshot e ausência de marcadores sintéticos.

Browser gate ainda pendente neste recibo.
