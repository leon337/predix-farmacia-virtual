# Passagens de bastão

1. **Mestre → Leonardo** — redefinir o requisito de produto real e operação simulada.
2. **Leonardo → Ricardo** — delimitar catálogo seguro: produtos para saúde, sem medicamentos, controlados ou itens invasivos/hospitalares.
3. **Ricardo → Sofia** — definir separação entre identidade real, preço ausente e operação simulada.
4. **Sofia → Manoel** — localizar fonte, validar hashes, modelar esquema e preparar carga transacional.
5. **Manoel → Renato** — executar ingestão no GitHub Actions e validar 500 registros.
6. **Renato → Emily** — auditar artefato; Emily bloqueou falso positivo de arquivos não rastreados.
7. **Emily → Renato** — corrigir detecção com `git status --porcelain` e repetir geração.
8. **Renato → Manoel** — entregar catálogo persistido no commit `be76a92a585158ad0a7a6b91d25b3aee65fa4230`.
9. **Manoel → Tiago** — atualizar API para preço nulo, registro Anvisa e identidade real.
10. **Tiago → Manoel** — API em estado de transição; autorizar carga somente após tratamento de preço ausente.
11. **Manoel → Ricardo** — primeira carga falhou por `pfv_products_name_key`; rollback verificado.
12. **Ricardo → Manoel** — substituir unicidade por nome pela identidade registro + nome + fabricante.
13. **Manoel → Gabriel e Laura** — banco real carregado; atualizar modo local e interface.
14. **Gabriel/Laura → Renato** — entregar frontend, servidor local e testes atualizados.
15. **Renato → Tiago** — smoke remoto encontrou busca incorreta por texto `registro`; API corrigida para extrair o número.
16. **Tiago → Renato** — API v3 ativa; repetição do mesmo smoke resultou em PASS.
17. **Renato → Miriam** — CI e smoke remoto aprovados; preparar deploy Render candidato.
18. **Miriam → Emily/Vinícius/Léo** — ainda pendente: browser evidence, PR, revisão e gate final.
