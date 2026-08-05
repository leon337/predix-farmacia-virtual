# Tiago — API e Funcionário Virtual

## Entrega

- `predix-api` versão 3;
- `catalogIdentity=real`;
- registro, processo, fabricante, detentor e classe de risco no produto;
- `priceCents=null` e `price='Consulte o estabelecimento'`;
- respostas distinguem produto real e estoque simulado;
- perguntas clínicas continuam em handoff;
- busca por número regulatório extraído da mensagem.

## Falha e correção

O primeiro smoke por frase `preço do registro ...` falhou porque a palavra `registro` permaneceu no termo. A versão 3 extrai diretamente sequências numéricas de 8 a 20 dígitos. O mesmo smoke passou na reexecução.
