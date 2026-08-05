'use strict';

const requestedView = new URLSearchParams(window.location.search).get('view');
if (requestedView && ['chat', 'catalog', 'reservation', 'reports'].includes(requestedView)) {
  window.addEventListener('DOMContentLoaded', () => setView(requestedView));
}
