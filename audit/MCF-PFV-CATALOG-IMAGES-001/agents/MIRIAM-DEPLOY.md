# Miriam — deploy

## Inspeção de infraestrutura

O serviço Render publica somente:

```text
public/index.html
public/styles.css
public/app.js
```

Essa inspeção bloqueou um candidato que dependia de `startup.js`, evitando deploy incompleto.

## Candidato final

```yaml
service_id: srv-d9pkpvu7bikc739i54u0
deploy_id: dep-d9ps19bncjis73f6iorg
sha: 4436983a9054180fca7dd46e2a1534f1aab13e67
status: live
url: https://predix-farmacia-virtual.onrender.com
```
