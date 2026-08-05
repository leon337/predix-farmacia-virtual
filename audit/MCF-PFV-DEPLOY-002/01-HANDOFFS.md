# Passagens de bastão — MCF-PFV-DEPLOY-002

## 1. Mestre → Sofia

- Entrada: screenshot do HTML bruto e ordem de continuar.
- Decisão: reabrir a missão como FAIL e substituir o frontend servido pela Edge Function.
- Saída: arquitetura estática separada da API.

## 2. Sofia → Gabriel

- Entrada: arquitetura Render Static Site + Supabase API.
- Ação esperada: cliente sem rotas relativas, sem administração pública e sem HTML gerado no runtime.
- Evidência: `public/index.html` e `public/app.js`.

## 3. Gabriel → Laura

- Entrada: estrutura funcional do cliente.
- Ação: responsividade, contraste, navegação móvel e aviso permanente de demonstração.
- Evidência: `public/styles.css`.

## 4. Manoel → Ricardo

- Entrada: chave administrativa exposta.
- Ação: inspecionar esquema real, corrigir consulta inicialmente inválida e localizar `value_hash`.
- Evidência: coluna bcrypt e evento de auditoria no PostgreSQL.

## 5. Ricardo → Miriam

- Entrada: credencial invalidada e painel administrativo removido.
- Decisão: publicar apenas atendimento, catálogo, reserva e relatórios.
- Evidência: hash aleatório irrecuperável e ausência de formulário administrativo em `public/index.html`.

## 6. Miriam → Renato

- Entrada: branch com frontend estático.
- Ação: criar serviço Render isolado e entregar URL candidata somente para validação.
- Evidência: serviço `srv-d9pkpvu7bikc739i54u0`, deploy `dep-d9pkq0e7bikc739i55sg` com estado `live`.

## 7. Renato → Tiago

- Entrada: novo site em validação.
- Ação de Renato: validar MIME, API, Chrome headless, DOM e screenshot móvel.
- Ação de Tiago: impedir que o endereço legado continue exibindo HTML bruto.
- Evidência: workflow run `31017058315`; Edge Function `predix-farmacia` versão 2 redirecionando ao Render.

## 8. Renato → Emily

- Entrada: artefato `predix-browser-evidence`.
- Evidência entregue: screenshot, DOM renderizado, health JSON e digest SHA-256 do ZIP.
- Resultado esperado: auditoria independente do conteúdo, não apenas do status do workflow.

## 9. Emily → Vinícius

- Entrada: candidato com evidências técnicas e visuais.
- Ação: revisão do diff, segurança, documentação e rastreabilidade antes do PR.

## 10. Vinícius → Léo

- Entrada: revisão sem bloqueios.
- Ação: gate operacional para merge e validação final da `main`.

## 11. Léo → Mestre

- Entrada: CI, browser smoke e revisão final.
- Saída: recibo de entrega somente após todos os gates em estado terminal.
