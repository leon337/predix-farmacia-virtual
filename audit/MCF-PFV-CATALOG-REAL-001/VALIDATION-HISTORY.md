# Histórico de validação

## Fonte e geração

- Fonte oficial da Anvisa: tentativa direta falhou por timeout no run `31021991343`, sem alteração de dados.
- Espelho separado de produtos para saúde: estrutura e hash confirmados no run `31022407792`.
- Run `31022641294`: validações passaram, mas Emily detectou falso positivo porque arquivos novos não foram versionados.
- Correção: `git status --porcelain`.
- Run `31022791987`: catálogo e relatório persistidos.
- SHA-256 do espelho: `d20df633de53a2c79a2efa03ebae61db72fcb7e27941f23993784f179130f173`.
- SHA-256 do catálogo: `322a842080af74e1cafeea0a98f0ea71a930ac442eadb1d6d9911e15b9b7cf34`.

## Banco PostgreSQL

- Arquivo fixado validado no banco: HTTP 200, 421.854 bytes, 500 produtos e hash exato.
- Primeira carga: FAIL por restrição antiga de nome único; rollback comprovado.
- Correção: identidade única por registro, nome e fabricante.
- Segunda carga: PASS — 500 identidades reais, 500 preços ausentes, 500 estoques e zero disponibilidade negativa.

## API e operações

- API v2 tratou preço nulo antes da carga.
- Primeiro smoke remoto falhou ao pesquisar frase contendo `registro`.
- API v3 extrai diretamente o número regulatório.
- Reexecução do mesmo smoke: PASS.
- Reservas continuam simuladas e retornam `totalCents: null`; o smoke cria e cancela a reserva.

## Modo local e candidato

- Modo SQLite passou a carregar o mesmo JSON hashado.
- CI do candidato `31025325789`: SUCCESS.
- Remote Deploy Smoke `31025325176`: SUCCESS.

## Render e navegador

- Primeiro browser run `31024993042`: FAIL porque recebeu frontend anterior do cache enquanto o deploy ainda compilava.
- Gate corrigido para aguardar marcador do candidato e romper cache por SHA.
- Deploy corrigido `dep-d9pm91egekts73dq8dqg`: live no SHA `88f7cae97a41f492cf03aa3e626ef8ef32429f5e`.
- Browser run `31025386429`, job `92372367944`: SUCCESS.
- Artefato `8938372627`: screenshot, DOM, HTML implantado, health e produto.
- Emily abriu e inspecionou o pacote fora do workflow: PASS_WITH_RECORDED_DEVIATIONS.

## Próximo gate

Abrir PR, revisar o diff, aguardar CI/remote/browser do PR, executar gate de Léo e integrar somente no SHA aprovado.
