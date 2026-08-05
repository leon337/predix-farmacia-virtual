# Predix Farmácia Virtual

MVP funcional de uma farmácia digital **inteiramente fictícia** para treinamento e validação do Funcionário Virtual especializado da Predix.

> O sistema não é uma farmácia real, não vende medicamentos, não processa pagamentos ou receitas e não fornece orientação clínica.

## Acesso público

- Interface: https://predix-farmacia-virtual.onrender.com
- Health da API: https://qylqyhxpwffiripcpjej.supabase.co/functions/v1/predix-api/api/health

O endereço Supabase antigo do frontend redireciona para a interface Render.

## Entregas do MVP

- empresa fictícia identificada como demonstração;
- catálogo determinístico com 500 produtos sintéticos;
- preços e estoque persistidos em PostgreSQL;
- reservas simuladas com proteção contra estoque negativo;
- conversas, consultas e auditoria básica;
- Funcionário Virtual com política de não invenção;
- encaminhamento de dúvidas clínicas ou sem fonte;
- interface pública responsiva;
- testes locais, smoke remoto e validação em Chrome headless.

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

O Funcionário Virtual pertence à Predix. A farmácia fornece treinamento e dados demonstrativos.

## Segurança

- tabelas `pfv_*` protegidas por RLS;
- funções transacionais restritas ao `service_role`;
- nenhum segredo versionado;
- área administrativa removida do frontend público;
- credencial administrativa anteriormente exposta foi invalidada;
- dados exclusivamente fictícios.

## Validação pública

O workflow `Browser Render Smoke` valida:

- `Content-Type: text/html`;
- health da API e 500 produtos;
- execução em Chrome headless;
- JavaScript carregando dados do PostgreSQL;
- ausência de HTML bruto visível;
- screenshot móvel armazenado como artefato.

A trilha da remediação está em `audit/MCF-PFV-DEPLOY-002/`.

## Executar localmente

Requisito: Python 3.12 ou superior.

```bash
python3 app.py
```

Acesse `http://127.0.0.1:8000`.

## Testar o servidor local

```bash
python3 -m unittest -v tests/test_mvp.py
```

## Limites

Sem WhatsApp real, pagamentos, receita médica, dados pessoais reais, recomendação de medicamentos ou vendas reais.
