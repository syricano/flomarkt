(function () {
  function qs(sel, root) { return (root || document).querySelector(sel); }
  function qsa(sel, root) { return Array.from((root || document).querySelectorAll(sel)); }

  function htmlToEl(html) {
    const div = document.createElement('div');
    div.innerHTML = html.trim();
    return div.firstElementChild;
  }

  function buildCard(idx) {
    // 1) take empty field HTML and retarget names/ids
    const emptyTpl = qs('#tpl-empty-fields');
    if (!emptyTpl) return null;
    const fieldsHtml = emptyTpl.innerHTML;
    const holder = document.createElement('div');
    holder.innerHTML = fieldsHtml;

    qsa('input,select', holder).forEach(function (el) {
      if (el.name) el.name = el.name.replace('__prefix__', idx);
      if (el.id)   el.id   = el.id.replace('__prefix__', idx);
      if (el.tagName === 'SELECT') el.selectedIndex = 0;
      if (el.type === 'text' || el.type === 'number') el.value = '';
      if (el.type === 'checkbox') el.checked = false;
    });

    const inputs = qsa('input,select', holder); // [DELETE, name, sku, price, color, size]

    // 2) inject into card template
    const cardTpl = qs('#tpl-product-card');
    if (!cardTpl) return null;
    const cardHtml = cardTpl.innerHTML
      .replace('__DELETE__', inputs[0].outerHTML)
      .replace('__NAME__',  inputs[1].outerHTML)
      .replace('__SKU__',   inputs[2].outerHTML)
      .replace('__PRICE__', inputs[3].outerHTML)
      .replace('__COLOR__', inputs[4].outerHTML)
      .replace('__SIZE__',  inputs[5].outerHTML);

    return htmlToEl(cardHtml);
  }

  function addCard(container) {
    const totalEl = qs('#id_products-TOTAL_FORMS');
    if (!totalEl) return;
    const idx = parseInt(totalEl.value || '0', 10);
    const card = buildCard(idx);
    if (!card) return;
    qs('#product-cards', container).appendChild(card);
    totalEl.value = idx + 1;
  }

  function removeCard(btn) {
    const card = btn.closest('.card');
    if (!card) return;
    const del = card.querySelector('input[type="checkbox"][name$="DELETE"]');
    if (del) del.checked = true;
    card.classList.add('d-none');
  }

  function wireProducts() {
    const wrap = qs('#products-card');
    if (!wrap) return;

    // Delegate clicks
    wrap.addEventListener('click', function (e) {
      const add = e.target.closest('.js-add-product');
      if (add) { addCard(wrap); return; }

      const rm = e.target.closest('.js-remove-product');
      if (rm) { removeCard(rm); }
    });
  }

  document.addEventListener('DOMContentLoaded', wireProducts);
})();
