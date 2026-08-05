'use strict';

const API_BASE = 'https://qylqyhxpwffiripcpjej.supabase.co/functions/v1/predix-api';
const state = { page: 1, totalPages: 1, sessionId: crypto.randomUUID() };

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

async function loadCompany() {
  const [company, health] = await Promise.all([api('/api/company'), api('/api/health')]);
  document.querySelector('#company-name').textContent = company.name;
  document.querySelector('#company-status').textContent = `${company.openingHours} • ${health.realProducts} produtos reais • PostgreSQL conectado`;

  const details = document.querySelector('#company-details');
  details.replaceChildren();
  [
    ['Endereço demonstrativo', company.address],
    ['Telefone demonstrativo', company.phone],
    ['Funcionamento', company.openingHours],
    ['Pagamentos simulados', company.payments],
    ['Entregas simuladas', company.delivery],
    ['Catálogo', `${health.realProducts} identidades reais; preços comerciais não cadastrados`],
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
    if (result.data?.product) {
      document.querySelector('#reservation-product').value = result.data.product.id;
      document.querySelector('#reservation-quantity').value = result.data.quantity || 1;
    }
  } catch (error) {
    addMessage('assistant', `Falha controlada: ${error.message}`);
  } finally {
    submit.disabled = false;
    input.focus();
  }
});

function productCard(product) {
  const card = document.createElement('article');
  card.className = 'product-card';
  card.append(textElement('span', `${product.sku} • ID ${product.id}`, 'tag'));
  card.append(textElement('h3', product.name));
  card.append(textElement('p', `${product.category} • ${product.manufacturer}`));
  card.append(textElement('p', `Apresentação técnica: ${product.presentation}`));
  card.append(textElement('p', `Registro Anvisa: ${product.anvisaRegistration} • Classe de risco: ${product.riskClass}`));

  const meta = document.createElement('div');
  meta.className = 'product-meta';
  meta.append(textElement('strong', product.price));
  meta.append(textElement(
    'span',
    product.quantityAvailable > 0
      ? `${product.quantityAvailable} no estoque demonstrativo`
      : 'Sem estoque demonstrativo',
    product.quantityAvailable > 0 ? 'stock-ok' : 'stock-zero',
  ));
  card.append(meta);
  card.append(textElement('small', 'Identidade do produto: real • Operação: simulada'));

  const reserve = textElement('button', 'Preparar reserva simulada');
  reserve.type = 'button';
  reserve.disabled = product.quantityAvailable < 1;
  reserve.addEventListener('click', () => {
    document.querySelector('#reservation-product').value = product.id;
    document.querySelector('#reservation-quantity').value = 1;
    setView('reservation');
    document.querySelector('#reservation-customer').focus();
  });
  card.append(reserve);
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

  document.querySelector('#catalog-count').textContent = `${result.total} produtos reais`;
  document.querySelector('#catalog-grid').replaceChildren(...result.items.map(productCard));
  document.querySelector('#page-status').textContent = `Página ${result.page} de ${state.totalPages}`;
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

function showResult(selector, message, error = false) {
  const target = document.querySelector(selector);
  target.textContent = message;
  target.classList.toggle('error', error);
}

document.querySelector('#reservation-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = {
    customerName: document.querySelector('#reservation-customer').value.trim(),
    items: [{
      productId: Number(document.querySelector('#reservation-product').value),
      quantity: Number(document.querySelector('#reservation-quantity').value),
    }],
  };

  try {
    const result = await api('/api/reservations', {
      method: 'POST',
      headers: { 'Idempotency-Key': crypto.randomUUID() },
      body: JSON.stringify(payload),
    });
    const totalLine = result.totalCents === null || result.totalCents === undefined
      ? 'Total: indisponível — preço comercial não cadastrado'
      : `Total demonstrativo: R$ ${(result.totalCents / 100).toFixed(2).replace('.', ',')}`;
    showResult(
      '#reservation-result',
      `Reserva ${result.id}\nStatus: ${result.status}\nValidade: ${result.expiresAt}\n${totalLine}\nNenhuma venda ou cobrança foi realizada.`,
    );
  } catch (error) {
    showResult('#reservation-result', error.message, true);
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
    ['Produtos reais', report.realIdentityProducts],
    ['Preços não cadastrados', report.productsWithoutPrice],
    ['Atendimentos', report.totalAttendances],
    ['Reservas simuladas', report.reservations],
    ['Encaminhamentos', report.handoffs],
    ['Sem estoque demonstrativo', report.outOfStockProducts],
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
