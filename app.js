const state = { page: 1, totalPages: 1, sessionId: crypto.randomUUID() };

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || data.message || `Erro HTTP ${response.status}`);
  return data;
}

function textElement(tag, text, className = '') {
  const element = document.createElement(tag);
  element.textContent = text;
  if (className) element.className = className;
  return element;
}

async function loadCompany() {
  const company = await api('/api/company');
  document.querySelector('#company-name').textContent = company.name;
  document.querySelector('#company-status').textContent = `${company.openingHours} • Dados fictícios`;
  const details = document.querySelector('#company-details');
  details.replaceChildren();
  [
    ['Endereço', company.address],
    ['Telefone', company.phone],
    ['Funcionamento', company.openingHours],
    ['Pagamentos', company.payments],
    ['Entregas', company.delivery],
  ].forEach(([label, value]) => {
    const item = document.createElement('div');
    item.append(textElement('strong', label), textElement('span', value));
    details.append(item);
  });
}

function activateView(name) {
  document.querySelectorAll('.tab').forEach((button) => button.classList.toggle('active', button.dataset.view === name));
  document.querySelectorAll('.view').forEach((view) => {
    const active = view.id === `view-${name}`;
    view.classList.toggle('active', active);
    view.hidden = !active;
  });
  if (name === 'catalog') loadCatalog().catch(showGlobalError);
  if (name === 'reports') loadReports().catch(showGlobalError);
}

document.querySelectorAll('.tab').forEach((button) => button.addEventListener('click', () => activateView(button.dataset.view)));

function addMessage(role, message, sources = [], handoff = false) {
  const container = document.querySelector('#chat-log');
  const item = document.createElement('div');
  item.className = `message ${role}`;
  item.append(textElement('strong', role === 'user' ? 'Você' : 'Funcionário Virtual'));
  item.append(textElement('p', message));
  if (sources.length) item.append(textElement('small', `Fontes: ${sources.join(', ')}`));
  if (handoff) item.append(textElement('small', ' • Encaminhamento humano fictício registrado'));
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
      const product = result.data.product;
      document.querySelector('#reservation-product').value = product.id;
      if (result.data.quantity) document.querySelector('#reservation-quantity').value = result.data.quantity;
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
  card.append(textElement('p', `${product.activeIngredient} • ${product.presentation}`));
  const meta = document.createElement('div');
  meta.className = 'product-meta';
  meta.append(textElement('strong', product.price));
  meta.append(textElement('span', product.quantityAvailable > 0 ? `${product.quantityAvailable} disponíveis` : 'Sem estoque', product.quantityAvailable > 0 ? 'stock-ok' : 'stock-zero'));
  card.append(meta);
  if (product.prescriptionRequired) card.append(textElement('span', 'Exige receita em operação real — somente simulação', 'tag'));
  const reserve = textElement('button', 'Preparar reserva');
  reserve.type = 'button';
  reserve.disabled = product.quantityAvailable < 1;
  reserve.addEventListener('click', () => {
    document.querySelector('#reservation-product').value = product.id;
    document.querySelector('#reservation-quantity').value = 1;
    activateView('inventory');
    document.querySelector('#reservation-customer').focus();
  });
  card.append(reserve);
  return card;
}

async function loadCatalog() {
  const query = encodeURIComponent(document.querySelector('#catalog-query').value.trim());
  const result = await api(`/api/products?query=${query}&page=${state.page}&pageSize=24`);
  state.totalPages = Math.max(1, result.totalPages);
  if (state.page > state.totalPages) { state.page = state.totalPages; return loadCatalog(); }
  document.querySelector('#catalog-count').textContent = `${result.total} produtos`;
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
document.querySelector('#prev-page').addEventListener('click', () => { if (state.page > 1) { state.page -= 1; loadCatalog().catch(showGlobalError); } });
document.querySelector('#next-page').addEventListener('click', () => { if (state.page < state.totalPages) { state.page += 1; loadCatalog().catch(showGlobalError); } });

function showResult(selector, message, error = false) {
  const target = document.querySelector(selector);
  target.textContent = message;
  target.classList.toggle('error', error);
}

document.querySelector('#reservation-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = {
    customerName: document.querySelector('#reservation-customer').value,
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
    const total = `R$ ${(result.totalCents / 100).toFixed(2).replace('.', ',')}`;
    showResult('#reservation-result', `Reserva ${result.id}\nStatus: ${result.status}\nValidade: ${result.expiresAt}\nTotal simulado: ${total}`);
  } catch (error) {
    showResult('#reservation-result', error.message, true);
  }
});

document.querySelector('#stock-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const productId = Number(document.querySelector('#stock-product').value);
  try {
    const product = await api(`/api/admin/inventory/${productId}`, {
      method: 'POST',
      headers: { 'X-Admin-Key': document.querySelector('#admin-key').value },
      body: JSON.stringify({ quantityTotal: Number(document.querySelector('#stock-quantity').value) }),
    });
    showResult('#stock-result', `${product.name}: total ${product.quantityTotal}, reservado ${product.quantityReserved}, disponível ${product.quantityAvailable}.`);
  } catch (error) {
    showResult('#stock-result', error.message, true);
  }
});

function table(headers, rows) {
  const element = document.createElement('table');
  const head = document.createElement('thead');
  const headRow = document.createElement('tr');
  headers.forEach((header) => headRow.append(textElement('th', header)));
  head.append(headRow);
  const body = document.createElement('tbody');
  rows.forEach((values) => {
    const row = document.createElement('tr');
    values.forEach((value) => row.append(textElement('td', String(value))));
    body.append(row);
  });
  element.append(head, body);
  return element;
}

async function loadReports() {
  const report = await api('/api/reports');
  const cards = [
    ['Atendimentos', report.totalAttendances],
    ['Reservas', report.reservations],
    ['Encaminhamentos', report.handoffs],
    ['Sem estoque', report.outOfStockProducts],
  ];
  document.querySelector('#report-cards').replaceChildren(...cards.map(([label, value]) => {
    const card = document.createElement('div');
    card.className = 'report-card';
    card.append(textElement('span', label), textElement('strong', String(value)));
    return card;
  }));
  document.querySelector('#top-products').replaceChildren(table(['Produto', 'Consultas'], report.mostQueriedProducts.map((item) => [item.name, item.queries])));
}

document.querySelector('#refresh-reports').addEventListener('click', () => loadReports().catch(showGlobalError));

function showGlobalError(error) {
  document.querySelector('#company-status').textContent = `Falha controlada: ${error.message}`;
}

Promise.all([loadCompany(), loadCatalog()]).catch(showGlobalError);
