# Manifesto de evidências — catálogo real

## Catálogo

- artefato: `data/real_products.json`
- produtos: `500`
- identidade: nome, fabricante, detentor, processo e registro reais
- preço comercial: ausente
- operação: simulada
- SHA-256 do espelho: `d20df633de53a2c79a2efa03ebae61db72fcb7e27941f23993784f179130f173`
- SHA-256 do catálogo: `322a842080af74e1cafeea0a98f0ea71a930ac442eadb1d6d9911e15b9b7cf34`
- commit de dados: `be76a92a585158ad0a7a6b91d25b3aee65fa4230`

## PostgreSQL e API

- produtos: `500`
- identidades reais: `500`
- preços ausentes: `500`
- disponibilidade negativa: `0`
- API: `predix-api` versão `3`
- digest da API: `54801b70043a895976f7bce0ef1b6a446d8dc5635c23946995d8e4ffb28a3c66`

## Candidato

- SHA: `88f7cae97a41f492cf03aa3e626ef8ef32429f5e`
- CI: run `31025325789` — `SUCCESS`
- Remote Deploy Smoke: run `31025325176` — `SUCCESS`
- Browser Render Smoke: run `31025386429`, job `92372367944` — `SUCCESS`

## Render

- service: `srv-d9pkpvu7bikc739i54u0`
- deploy: `dep-d9pm91egekts73dq8dqg`
- SHA publicado: `88f7cae97a41f492cf03aa3e626ef8ef32429f5e`
- estado: `live`

## Pacote de navegador

- artifact: `8938372627`
- digest: `sha256:4d8400aa262f7a2e0a9e0346dd30398fef0948d0b85f512983455cd75318f355`

```text
aabc2b4fab494103eae2aa3e7d2120cbdc3d6354f35d798eb79faf03d9005ce4  deployed.html
d34b60a55c2a1649a06da1407e7e6ffa1af348ef9dce1c97832fab311d3ae58b  health.json
7faa0c5ead35c423598bcc302e478ec83222b46242d69caf5755bfc32700cd4e  predix-mobile-real-catalog.png
8baad8b51a35fd45a7ef2327db60d4b5ef739699142fe63232719a4a0f4dc0d0  product.json
b4e7d84df6f7cb8e835bf6bc7f29dd588029e2bedc3045459e9a2abe57bb10dc  rendered.html
```

## Inspeção independente

Emily abriu o screenshot, o DOM, o health e o produto fora do workflow. Confirmou interface móvel renderizada, 500 produtos reais, registro Anvisa, preço ausente, operação simulada, ausência de HTML bruto e ausência de marcadores sintéticos.
