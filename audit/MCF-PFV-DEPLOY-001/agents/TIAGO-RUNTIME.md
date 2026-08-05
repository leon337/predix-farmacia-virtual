# Tiago — Runtime do Funcionário Virtual

## API publicada

- Função: `predix-api`
- ID: `e79d8e88-9b38-4ce2-92c0-50ca4395ab84`
- Versão: `1`
- Estado: `ACTIVE`
- Bundle SHA-256: `8b399c5c04b5b5f602178e99168b34a20c14150a13f9998dfa06cf72067602a3`

## Interface publicada

- Função: `predix-farmacia`
- ID: `32592948-ed44-4faa-b853-524647f6f617`
- Versão: `1`
- Estado: `ACTIVE`
- Bundle SHA-256: `21e25383ac0903fd6579f5d81cb592e4268208b7580b39ee1d5e1482132f938b`

## Capacidades remotas

- health check;
- dados da empresa;
- catálogo paginado e pesquisável;
- consulta de preço e estoque;
- Funcionário Virtual com fontes e encaminhamento;
- reserva transacional e idempotente;
- cancelamento;
- relatórios;
- administração de estoque protegida por chave.

## Política de resposta

O runtime responde fatos somente após consulta ao PostgreSQL ou às regras autorizadas. Perguntas clínicas, perguntas sem fonte e intenções não suportadas geram encaminhamento humano fictício.
