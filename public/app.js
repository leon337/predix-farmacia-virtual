'use strict';

const API_BASE = 'https://qylqyhxpwffiripcpjej.supabase.co/functions/v1/predix-api';
const state = {
  page: 1,
  totalPages: 1,
  sessionId: crypto.randomUUID(),
  health: null,
};

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || data.message || `Erro HTTP ${response.status}`);
  return data;
}

function textElement(tag, text, className = '') {
  const element = document.createElement(tag);
  element.textContent = String(text ?? '');
  if (className) element.className = className;
  return element;
}

function placeholderImage(name) {
  const safeName = String(name || 'Produto').slice(0, 36).replace(/[<>&"']/g, '');
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="640" height="480" viewBox="0 0 640 480"><rect width="640" height="480" fill="#f5f8f6"/><path d="M230 150h180v180H230z" fill="#d4e7da"/><path d="M265 190h110v100H265z" fill="#fff" stroke="#176b43" stroke-width="12"/><path d="M320 210v60M290 240h60" stroke="#176b43" stroke-width="15" stroke-linecap="round"/><text x="320" y="380" text-anchor="middle" font-family="Arial,sans-serif" font-size="24" fill="#0f5132">${safeName}</text></svg>`;
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}

function setView(name) {
  document.querySelectorAll('.tab').forEach((button) => {
    button.classList.toggle('active', button.dataset.view === name);
  });
  document.querySelectorAll('.view').forEach((view) => {
    const active = view.id === `view-${name}`;
    view.classList.toggle('active', active);
    view.hidden = !active;
  });
  if (name === 'catalog') loadCatalog().catch(showGlobalError);
  if (name === 'reports') loadReports().catch(showGlobalError);
}

document.querySelectorAll('.tab').forEach((button) => {
  button.addEventListener('click', () => setView(button.dataset.view));
});

function updateCatalogSummary(health) {
  state.health = health;
  document.querySelector('#summary-products').textContent = health.distinctProducts ?? health.productRecords ?? 0;
  document.querySelector('#summary-images').textContent = health.productsWithImages ?? 0;
  document.querySelector('#summary-stock').textContent = Number(health.stockUnitsSimulated ?? 0).toLocaleString('pt-BR');
}

async function loadCompany() {
  const [company, health] = await Promise.all([api('/api/company'), api('/api/health')]);
  updateCatalogSummary(health);
  document.querySelector('#company-name').textContent = company.name;
  document.querySelector('#company-status').textContent = `${health.distinctProducts} produtos distintos • ${Number(health.stockUnitsSimulated).toLocaleString('pt-BR')} unidades simuladas • PostgreSQL conectado`;

  const details = document.querySelector('#company-details');
  details.replaceChildren();
  [
    ['Endereço demonstrativo', company.address],
    ['Telefone demonstrativo', company.phone],
    ['Funcionamento', company.openingHours],
    ['Produtos cadastrados', `${health.distinctProducts} produtos distintos`],
    ['Imagens cadastradas', `${health.productsWithImages} produtos com imagem`],
    ['Estoque demonstrativo', `${Number(health.stockUnitsSimulated).toLocaleString('pt-BR')} unidades simuladas`],
    ['Operações públicas', 'Consulta informativa; sem venda ou reserva'],
  ].forEach(([label, value]) => {
    const item = document.createElement('div');
    item.append(textElement('strong', label), textElement('span', value));
    details.append(item);
  });
}

function addMessage(role, message, sources = [], handoff = false) {
  const container = document.querySelector('#chat-log');
  const item = document.createElement('div');
  item.className = `message ${role}`;
  item.append(textElement('strong', role === 'user' ? 'Você' : 'Funcionário Virtual'));
  item.append(textElement('p', message));
  if (sources.length) item.append(textElement('small', `Fontes: ${sources.join(', ')}`));
  if (handoff) item.append(textElement('small', 'Encaminhamento humano demonstrativo registrado'));
  container.append(item);
  container.scrollTop = container.scrollHeight;
}

document.querySelector('#chat-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const input = document.querySelector('#chat-input');
  const message = input.value.trim();
  if (!message) return;
  addMessage('user', message);
  input.value = '';
  const submit = event.submitter;
  submit.disabled = true;
  try {
    const result = await api('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ message, sessionId: state.sessionId }),
    });
    addMessage('assistant', result.message, result.sources || [], result.handoffRequired);
  } catch (error) {
    addMessage('assistant', `Falha controlada: ${error.message}`);
  } finally {
    submit.disabled = false;
    input.focus();
  }
});

function productImage(product) {
  const wrap = document.createElement('div');
  wrap.className = 'product-image-wrap';

  const image = document.createElement('img');
  image.className = 'product-image';
  image.alt = `Imagem do produto ${product.name}`;
  image.loading = 'lazy';
  image.decoding = 'async';
  image.referrerPolicy = 'no-referrer';
  image.src = product.imageUrl || placeholderImage(product.name);
  image.dataset.realSource = product.imageUrl ? 'true' : 'false';
  image.addEventListener('error', () => {
    image.dataset.loadError = 'true';
    image.src = placeholderImage(product.name);
  }, { once: true });

  wrap.append(image);
  return wrap;
}

function detailRow(label, value) {
  const row = document.createElement('div');
  row.append(textElement('dt', label), textElement('dd', value || 'Não informado'));
  return row;
}

function productCard(product, position) {
  const card = document.createElement('article');
  card.className = 'product-card';
  card.dataset.productId = String(product.id);
  card.dataset.hasImage = product.imageUrl ? 'true' : 'false';
  card.append(productImage(product));

  const body = document.createElement('div');
  body.className = 'product-card-body';

  const identity = product.barcode
    ? `GTIN ${product.barcode}`
    : product.anvisaRegistration
      ? `ANVISA ${product.anvisaRegistration}`
      : product.sku;

  body.append(textElement('span', `${identity} • Produto ${position} de ${state.health?.distinctProducts ?? 500}`, 'tag'));
  body.append(textElement('h3', product.name));
  body.append(textElement('p', `${product.category || 'Categoria não informada'} • ${product.manufacturer || 'Fabricante não informado'}`, 'product-subtitle'));

  const details = document.createElement('dl');
  details.className = 'product-details';
  details.append(detailRow('Apresentação', product.presentation));
  if (product.barcode) details.append(detailRow('Código de barras', product.barcode));
  if (product.anvisaRegistration) details.append(detailRow('Registro Anvisa', product.anvisaRegistration));
  if (product.imageSource) details.append(detailRow('Fonte da imagem', product.imageSource));
  body.append(details);

  const meta = document.createElement('div');
  meta.className = 'product-meta';
  meta.append(textElement('strong', product.price));
  meta.append(textElement(
    'span',
    product.quantityAvailable > 0
      ? `${product.quantityAvailable} unidades simuladas disponíveis`
      : 'Sem unidades simuladas disponíveis',
    product.quantityAvailable > 0 ? 'stock-ok' : 'stock-zero',
  ));
  body.append(meta);
  body.append(textElement('small', 'Cadastro informativo • Estoque e operação simulados • Sem venda ou reserva', 'operation-note'));

  card.append(body);
  return card;
}

async function loadCatalog() {
  const query = encodeURIComponent(document.querySelector('#catalog-query').value.trim());
  const result = await api(`/api/products?query=${query}&page=${state.page}&pageSize=24`);
  state.totalPages = Math.max(1, result.totalPages);

  if (state.page > state.totalPages) {
    state.page = state.totalPages;
    return loadCatalog();
  }

  document.querySelector('#catalog-count').textContent = `${result.total} produtos distintos`;
  const cards = result.items.map((product, index) => productCard(product, result.firstRecord + index));
  document.querySelector('#catalog-grid').replaceChildren(...cards);
  document.querySelector('#page-status').textContent = `Produtos ${result.firstRecord}–${result.lastRecord} de ${result.total} • Página ${result.page} de ${state.totalPages}`;
  document.querySelector('#prev-page').disabled = state.page <= 1;
  document.querySelector('#next-page').disabled = state.page >= state.totalPages;
}

document.querySelector('#catalog-form').addEventListener('submit', (event) => {
  event.preventDefault();
  state.page = 1;
  loadCatalog().catch(showGlobalError);
});

document.querySelector('#prev-page').addEventListener('click', () => {
  if (state.page > 1) {
    state.page -= 1;
    loadCatalog().catch(showGlobalError);
  }
});

document.querySelector('#next-page').addEventListener('click', () => {
  if (state.page < state.totalPages) {
    state.page += 1;
    loadCatalog().catch(showGlobalError);
  }
});

function buildTable(headers, rows) {
  const table = document.createElement('table');
  const head = document.createElement('thead');
  const headerRow = document.createElement('tr');
  headers.forEach((header) => headerRow.append(textElement('th', header)));
  head.append(headerRow);

  const body = document.createElement('tbody');
  rows.forEach((values) => {
    const row = document.createElement('tr');
    values.forEach((value) => row.append(textElement('td', value)));
    body.append(row);
  });
  table.append(head, body);
  return table;
}

async function loadReports() {
  const report = await api('/api/reports');
  const cards = [
    ['Produtos distintos', report.distinctProducts],
    ['Produtos com imagem', report.productsWithImages],
    ['Unidades simuladas', Number(report.stockUnitsSimulated || 0).toLocaleString('pt-BR')],
    ['Preços não cadastrados', report.productsWithoutPrice],
    ['Atendimentos', report.totalAttendances],
    ['Encaminhamentos', report.handoffs],
    ['Produtos sem estoque', report.outOfStockProducts],
  ];

  document.querySelector('#report-cards').replaceChildren(...cards.map(([label, value]) => {
    const card = document.createElement('div');
    card.className = 'report-card';
    card.append(textElement('span', label), textElement('strong', value));
    return card;
  }));

  const rows = (report.mostQueriedProducts || []).map((item) => [item.name, item.queries]);
  document.querySelector('#top-products').replaceChildren(buildTable(['Produto', 'Consultas'], rows));
}

document.querySelector('#refresh-reports').addEventListener('click', () => {
  loadReports().catch(showGlobalError);
});

function showGlobalError(error) {
  document.querySelector('#company-status').textContent = `Falha controlada: ${error.message}`;
}

Promise.all([loadCompany(), loadCatalog()]).catch(showGlobalError);
