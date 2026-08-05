# Predix Farmácia Virtual

MVP funcional de uma farmácia digital **inteiramente fictícia** para treinamento, testes e validação do primeiro Funcionário Virtual especializado da Predix.

> O sistema não é uma farmácia real, não vende medicamentos, não processa pagamentos ou receitas e não fornece orientação clínica.

## Objetivo validado

Demonstrar que um Funcionário Virtual pode atuar como balconista digital consultando dados e regras antes de responder, em vez de funcionar como chatbot genérico.

## Entregas do MVP

- empresa fictícia identificada como demonstração;
- seed determinístico com 500 produtos sintéticos;
- catálogo, preços e estoque;
- reservas simuladas com proteção contra estoque negativo;
- auditoria básica;
- oito documentos em `treinamento/`;
- Funcionário Virtual com política de não invenção;
- encaminhamento de dúvidas clínicas ou sem fonte;
- interface web com chat, catálogo, reservas e relatórios;
- testes automatizados e CI.

## Arquitetura

```text
Funcionário Virtual Predix
        │
        ├── conhecimento permanente: treinamento/*.md
        └── dados dinâmicos: SQLite (produtos, preços, estoque e reservas)
```

O funcionário pertence à Predix. A farmácia fornece apenas treinamento e dados, permitindo reutilizar o mesmo núcleo em outras empresas.

## Executar

Requisito: Python 3.12 ou superior. Não há dependências externas.

```bash
python app.py
```

Acesse `http://127.0.0.1:8000`.

Na primeira execução, o banco `data/predix.db` é criado e recebe 500 produtos fictícios.

## Testar

```bash
python -m unittest -v tests/test_mvp.py
```

## Administração de estoque

Configure uma chave antes de iniciar:

```bash
PREDIX_ADMIN_KEY='chave-local-forte' python app.py
```

A atualização administrativa exige o cabeçalho `X-Admin-Key`.

## Endpoints

- `GET /api/health`
- `GET /api/company`
- `GET /api/products?query=&page=&pageSize=`
- `POST /api/chat`
- `POST /api/reservations` com `Idempotency-Key`
- `POST /api/reservations/{id}/cancel`
- `GET /api/reports`
- `POST /api/admin/inventory/{productId}`

## Limites do MVP

Sem WhatsApp real, pagamentos, receita médica, dados pessoais reais, recomendação de medicamentos ou publicação automática em produção.
