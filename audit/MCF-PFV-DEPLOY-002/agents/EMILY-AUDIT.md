# Emily — Auditoria independente

## Materiais recebidos

- pacote ZIP produzido pelo GitHub Actions;
- `predix-mobile.png`;
- `rendered.html`;
- `health.json`;
- logs por etapa do job `92343746550`;
- registros de rotação da credencial;
- versão 2 do redirecionamento legado.

## Verificações realizadas

1. Descompactação do artefato fora do workflow.
2. Conferência de tamanhos:
   - screenshot: 69.593 bytes;
   - DOM: 14.869 bytes;
   - health: 93 bytes.
3. Conferência do JSON: `status=ok`, `products=500`, `database=supabase-postgres`.
4. Busca no DOM por `PostgreSQL conectado` e `500 produtos`.
5. Inspeção visual da captura móvel.
6. Conferência dos hashes locais contra o manifesto.
7. Verificação de ausência do painel administrativo no novo frontend.
8. Verificação de que o endereço legado foi substituído por redirect.

## Resultado visual

A imagem mostra elementos renderizados: cabeçalho, nome da empresa, aviso de demonstração, status PostgreSQL, banner de segurança, abas e balcão digital. Não mostra código-fonte bruto.

## Desvios preservados

- o primeiro deploy foi declarado válido por um teste insuficiente;
- a chave administrativa foi exposta e precisou ser invalidada;
- uma consulta inicial ao esquema usou coluna inexistente, sem escrita;
- a nova auditoria ocorre em missão reaberta e não apaga os erros anteriores.

## Parecer

`PASS_WITH_RECORDED_DEVIATIONS`

O candidato corretivo pode seguir para revisão de PR. A aprovação é limitada ao frontend público, integração com API, persistência demonstrativa e segurança descritas neste pacote.

## Handoff

Entregue a Vinícius para revisão de mudanças e a Léo para gate operacional após CI do PR.
