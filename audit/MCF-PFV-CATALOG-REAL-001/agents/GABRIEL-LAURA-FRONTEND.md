# Gabriel e Laura — frontend e modo local

## Frontend

- remove `CATÁLOGO SINTÉTICO` e exemplos Demo;
- mostra registro Anvisa, classe, fabricante e apresentação;
- exibe `Consulte o estabelecimento` para preço ausente;
- identifica estoque e reserva como demonstrativos;
- rodapé separa produto real de operação simulada;
- reserva aceita `totalCents=null`.

## Modo local

- `app.py` lê o mesmo JSON hashado;
- SQLite contém 500 identidades reais;
- servidor entrega os arquivos de `public/`;
- gerador de nomes sintéticos foi removido;
- inicialização migra banco antigo e é idempotente.
