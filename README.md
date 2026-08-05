# Predix Farmácia Virtual

MVP funcional para treinamento e validação do Funcionário Virtual especializado da Predix.

O catálogo contém **500 produtos para saúde com identidade regulatória real**: nome, fabricante, detentor, processo e registro provenientes de base derivada dos dados abertos da Anvisa. A empresa, o estoque, os clientes, as reservas, os pagamentos, as entregas e todas as operações continuam simulados.

> O sistema não é uma farmácia real, não vende medicamentos, não processa pagamentos ou receitas e não fornece orientação clínica. Medicamentos, produtos controlados e itens invasivos ou hospitalares foram excluídos desta carga.

## Acesso público

- Interface: https://predix-farmacia-virtual.onrender.com
- Health da API: https://qylqyhxpwffiripcpjej.supabase.co/functions/v1/predix-api/api/health

O endereço Supabase antigo do frontend redireciona para a interface Render.

## Entregas do MVP

- empresa fictícia identificada como demonstração;
- catálogo versionado com 500 identidades reais de produtos para saúde;
- registro Anvisa, processo, fabricante, detentor e classe de risco;
- preços comerciais não cadastrados, sem valores inventados;
- estoque persistente, determinístico e demonstrativo;
- reservas simuladas com proteção contra estoque negativo;
- conversas, consultas e auditoria básica;
- Funcionário Virtual com política de não invenção;
- encaminhamento de dúvidas clínicas ou sem fonte;
- interface pública responsiva;
- testes locais, smoke remoto e validação em Chrome headless.

## Origem e rastreabilidade do catálogo

- Fonte original declarada: dados abertos de produtos para saúde da Anvisa;
- espelho público versionado usado por indisponibilidade temporária do servidor oficial;
- hash SHA-256 do espelho validado antes da geração;
- hash SHA-256 do catálogo validado antes da carga PostgreSQL;
- classes aceitas: I e II;
- medicamentos e itens invasivos/hospitalares excluídos;
- relatório: `audit/MCF-PFV-CATALOG-REAL-001/SOURCE-REPORT.md`;
- artefato: `data/real_products.json`.

## Arquitetura publicada

```text
Render Static Site
        │ HTTPS/CORS
        ▼
Supabase Edge API
        │ service_role
        ▼
Supabase PostgreSQL
```

O Funcionário Virtual pertence à Predix. Os produtos têm identidade real; a operação comercial é demonstrativa.

## Segurança

- tabelas `pfv_*` protegidas por RLS;
- funções transacionais restritas ao `service_role`;
- nenhum segredo versionado;
- área administrativa removida do frontend público;
- credencial administrativa anteriormente exposta foi invalidada;
- nenhuma venda, cobrança, entrega ou orientação de uso é executada;
- preços comerciais não foram inventados.

## Validação pública

Os workflows validam:

- `Content-Type: text/html`;
- health da API com 500 produtos e 500 identidades reais;
- registro Anvisa no retorno do catálogo;
- preço `null` e mensagem “Consulte o estabelecimento”;
- reserva e cancelamento demonstrativos sem total inventado;
- execução em Chrome headless;
- JavaScript carregando dados do PostgreSQL;
- ausência de HTML bruto visível;
- ausência de marcadores sintéticos;
- screenshot móvel armazenado como artefato.

As trilhas anteriores permanecem em `audit/MCF-PFV-DEPLOY-002/`. A correção do catálogo está em `audit/MCF-PFV-CATALOG-REAL-001/`.

## Executar localmente

Requisito: Python 3.12 ou superior.

```bash
python3 app.py
```

Acesse `http://127.0.0.1:8000`.

O modo local lê o mesmo arquivo `data/real_products.json` e valida seu SHA-256 antes de criar o banco SQLite.

## Testar o servidor local

```bash
python3 -m unittest -v tests/test_mvp.py
```

## Limites

Sem medicamentos, produtos controlados, WhatsApp real, pagamentos, receita médica, dados pessoais reais, recomendação clínica ou vendas reais.
