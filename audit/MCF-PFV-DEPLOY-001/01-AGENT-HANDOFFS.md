# Passagens de bastão — MCF-PFV-DEPLOY-001

| Ordem | Agente | Entrada recebida | Ação executada | Evidência produzida | Destino |
|---:|---|---|---|---|---|
| 1 | Mestre | autorização integral de Leandro | abriu contrato, critérios e risco Classe B | `00-MISSION-CONTRACT.md` | Léo e Sofia |
| 2 | Léo | contrato e autorização | aprovou execução sem nova interrupção humana | escopo fechado e fallback autorizado | Sofia |
| 3 | Sofia | código local e necessidade de acesso público | definiu PostgreSQL + Edge API + Edge Frontend | `agents/SOFIA-ARCHITECTURE.md` | Manoel |
| 4 | Manoel | arquitetura de persistência | criou schema `pfv_*`, constraints, seed e RPCs transacionais | migration `create_predix_farmacia_virtual_mvp` | Tiago e Ricardo |
| 5 | Tiago | banco e contratos | publicou `predix-api` e `predix-farmacia` | function IDs, versões e hashes | Ricardo e Renato |
| 6 | Ricardo | funções e permissões | executou advisor, bloqueou gate, revogou `PUBLIC/anon/authenticated` e revalidou | migration `harden_predix_rpc_permissions` | Renato |
| 7 | Renato | URLs públicas e critérios | executou smoke remoto independente no GitHub Actions | run `31013163332`, job `92330304228`, PASS | Vinícius e Emily |
| 8 | Vinícius | código, contratos e provas | revisou coerência entre API, banco e testes | checklist no PR | Gabriel |
| 9 | Gabriel | branch e evidências | prepara PR, exige CI verde e integra por squash | PR de deploy público | Emily e Léo |
| 10 | Emily | conjunto completo de recibos | audita existência, consistência e limites das evidências | `agents/EMILY-AUDIT.md` | Léo |
| 11 | Léo | auditoria e CI | decide gate final | `CHECKPOINT.yaml` | Mestre |
| 12 | Mestre | gate aprovado | fecha missão somente com URL pública e merge comprovados | recibo final no PR | Leandro |

## Falhas registradas

1. O Render recusou um segundo banco gratuito por limite da conta.
2. A restauração de outro projeto Supabase foi recusada pelo limite de projetos ativos.
3. Duas alterações temporárias foram feitas diretamente em `main`; uma foi removida e a segunda tornou-se apenas o diretório de auditoria. O desvio foi registrado e o restante da execução seguiu por branch e PR.
4. O advisor identificou RPCs herdando `EXECUTE` de `PUBLIC`; o gate foi bloqueado até a correção.
