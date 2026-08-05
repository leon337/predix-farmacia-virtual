# Arquitetura do MVP

## Princípio central

```text
Funcionário Virtual Predix
        │
        ├── treinamento permanente em Markdown
        └── ferramentas sobre dados dinâmicos da farmácia
```

O núcleo comportamental pertence à Predix. A empresa fornece conhecimento, regras e dados, permitindo treinar o mesmo funcionário para outro cliente.

## Componentes

- `app.py`: servidor HTTP, domínio, SQLite, APIs, orquestração do Funcionário Virtual e auditoria.
- `treinamento/`: conhecimento permanente da empresa.
- `index.html`, `styles.css`, `app.js`: chat, catálogo, estoque, reservas e relatórios.
- `tests/`: validação automatizada do MVP.

## Dados dinâmicos

Empresa, produtos, preços, estoque, reservas, conversas e auditoria ficam no SQLite. O seed determinístico cria exatamente 500 produtos sintéticos.

## Segurança e limites

- dados fictícios;
- sem vendas, pagamentos, receitas ou orientação clínica;
- reserva transacional e idempotente;
- estoque com restrições de integridade;
- administração protegida por chave;
- ausência de fonte causa encaminhamento, não invenção.
