/* COOGI Black Friday free cap: auto-add + colour picker.
   Adds one trucker cap to the cart when the shopper has another item,
   and lets them switch colour in the cart. The Shopify "Buy X get Y"
   discount is what makes the cap free. Remove after the sale. */
(function () {
  if (window.__coogiFreeCap) return;
  window.__coogiFreeCap = true;

  var END = new Date('2026-12-01T04:59:00Z'); // Nov 30, 11:59 PM ET
  if (new Date() > END) return;

  var CAPS = [
    { id: 51012734583036, name: 'Black', color: '#111111' },
    { id: 51012738580732, name: 'Navy', color: '#1b2550' },
    { id: 51012739236092, name: 'White', color: '#ffffff' }
  ];
  var DEFAULT_ID = CAPS[0].id;
  var CAP_IDS = CAPS.map(function (c) { return c.id; });
  var DECLINED = 'coogiFreeCapDeclined';
  var PROP = '_bf_free_cap';
  var busy = false;
  var hadCap = false;

  var rawFetch = window.fetch.bind(window);
  var JSON_POST = { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' } };

  function store(action, value) {
    try {
      if (action === 'get') return window.sessionStorage.getItem(DECLINED);
      if (action === 'set') window.sessionStorage.setItem(DECLINED, value);
      if (action === 'clear') window.sessionStorage.removeItem(DECLINED);
    } catch (e) {}
    return null;
  }
  function post(url, body) {
    var opts = { method: JSON_POST.method, headers: JSON_POST.headers, body: JSON.stringify(body) };
    return rawFetch(url, opts).then(function (r) { return r.json(); });
  }
  function getCart() {
    return rawFetch('/cart.js', { headers: { Accept: 'application/json' } }).then(function (r) { return r.json(); });
  }
  function isCap(item) { return CAP_IDS.indexOf(item.variant_id) > -1; }
  function isRealItem(item) {
    if (isCap(item)) return false;
    var label = ((item.product_title || '') + ' ' + (item.product_type || '') + ' ' + (item.vendor || '')).toLowerCase();
    return !/protection|navidium|insurance/.test(label);
  }
  function isAutoCap(item) { return isCap(item) && item.properties && item.properties[PROP]; }

  /* Re-render the theme's cart drawer, cart page and counter. */
  function refresh() {
    var sections = [];
    ['cart-drawer', 'cart-drawer-items', 'cart-items'].forEach(function (tag) {
      var el = document.querySelector(tag);
      if (!el || typeof el.getSectionsToRender !== 'function') return;
      try {
        el.getSectionsToRender().forEach(function (s) {
          if (s && s.section && !sections.some(function (x) { return x.id === s.id; })) sections.push(s);
        });
      } catch (e) {}
    });
    if (!sections.length) { decorate(); return Promise.resolve(); }
    var names = sections.map(function (s) { return s.section; }).filter(function (v, i, a) { return a.indexOf(v) === i; });
    return rawFetch(window.location.pathname + '?sections=' + encodeURIComponent(names.join(',')))
      .then(function (r) { return r.json(); })
      .then(function (data) {
        sections.forEach(function (s) {
          var html = data[s.section];
          if (!html) return;
          var doc = new DOMParser().parseFromString(html, 'text/html');
          var src = doc.querySelector(s.selector);
          var dst = document.querySelector(s.id);
          if (src && dst) dst.innerHTML = src.innerHTML;
        });
        decorate();
      })
      .catch(function () { decorate(); });
  }

  /* Keep the cart in the right state: one cap when there is something to buy. */
  function sync(afterShopperChange) {
    if (busy) return Promise.resolve();
    busy = true;
    return getCart().then(function (cart) {
      var caps = cart.items.filter(isCap);
      var real = cart.items.filter(isRealItem);

      if (!cart.items.length) store('clear');
      if (afterShopperChange && hadCap && !caps.length && real.length) store('set', '1'); // shopper removed it
      hadCap = caps.length > 0;

      if (real.length && !caps.length && !store('get')) {
        var props = {}; props[PROP] = 'Black Friday';
        return post('/cart/add.js', { items: [{ id: DEFAULT_ID, quantity: 1, properties: props }] })
          .then(function () { hadCap = true; return refresh(); });
      }
      if (!real.length && caps.length && caps.every(isAutoCap)) {
        var updates = {};
        caps.forEach(function (c) { updates[c.key] = 0; });
        return post('/cart/update.js', { updates: updates })
          .then(function () { hadCap = false; return refresh(); });
      }
      decorate();
    }).catch(function () {}).then(function () { busy = false; });
  }

  function swapTo(variantId) {
    if (busy) return;
    busy = true;
    getCart().then(function (cart) {
      var cap = cart.items.filter(isCap)[0];
      if (!cap || cap.variant_id === variantId) return;
      var props = {}; props[PROP] = 'Black Friday';
      return post('/cart/change.js', { id: cap.key, quantity: 0 })
        .then(function () { return post('/cart/add.js', { items: [{ id: variantId, quantity: 1, properties: props }] }); })
        .then(function () { hadCap = true; return refresh(); });
    }).catch(function () {}).then(function () { busy = false; });
  }

  /* Colour picker under the cap line in the cart drawer and cart page. */
  function decorate() {
    var items = document.querySelectorAll('.cart-item');
    for (var i = 0; i < items.length; i++) {
      var item = items[i];
      if (item.querySelector('.coogi-cap-pick')) continue;
      var link = item.querySelector('a[href*="variant="]');
      if (!link) continue;
      var m = (link.getAttribute('href') || '').match(/variant=(\d+)/);
      var current = m ? Number(m[1]) : 0;
      if (CAP_IDS.indexOf(current) === -1) continue;

      var box = document.createElement('div');
      box.className = 'coogi-cap-pick';
      box.style.cssText = 'margin:8px 0 6px;font-size:12px;line-height:1.3;';
      var label = document.createElement('div');
      label.textContent = 'Your free cap. Pick a color:';
      label.style.cssText = 'font-weight:600;margin-bottom:6px;';
      box.appendChild(label);
      var row = document.createElement('div');
      row.style.cssText = 'display:flex;gap:6px;flex-wrap:wrap;';
      CAPS.forEach(function (cap) {
        var b = document.createElement('button');
        b.type = 'button';
        b.setAttribute('aria-label', cap.name + ' cap');
        b.setAttribute('aria-pressed', cap.id === current ? 'true' : 'false');
        b.style.cssText = 'display:inline-flex;align-items:center;gap:6px;padding:6px 10px;border-radius:20px;cursor:pointer;font:inherit;font-size:12px;background:#fff;color:#111;border:' +
          (cap.id === current ? '2px solid #111;font-weight:700;' : '1px solid #bbb;');
        var dot = document.createElement('span');
        dot.style.cssText = 'width:12px;height:12px;border-radius:50%;border:1px solid #999;display:inline-block;background:' + cap.color + ';';
        b.appendChild(dot);
        b.appendChild(document.createTextNode(cap.name));
        b.addEventListener('click', function (ev) { ev.preventDefault(); ev.stopPropagation(); swapTo(cap.id); });
        row.appendChild(b);
      });
      box.appendChild(row);
      var host = item.querySelector('.cart-item__details') || item;
      var title = host.querySelector('.cart-item__title');
      if (title && title.nextSibling) host.insertBefore(box, title.nextSibling); else host.appendChild(box);
    }
  }

  /* Watch the shopper's own cart changes (theme, apps) and re-sync after them. */
  var timer = null;
  function queue() {
    clearTimeout(timer);
    timer = setTimeout(function () { sync(true); }, 450);
  }
  function isCartWrite(url) { return /\/cart\/(add|change|update|clear)(\.js)?(\?|$)/.test(String(url || '')); }

  window.fetch = function (input, init) {
    var url = typeof input === 'string' ? input : (input && input.url);
    var p = rawFetch(input, init);
    if (isCartWrite(url)) p.then(queue, function () {});
    return p;
  };
  var xhrOpen = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function (method, url) {
    if (isCartWrite(url)) this.addEventListener('loadend', queue);
    return xhrOpen.apply(this, arguments);
  };

  if (window.MutationObserver) {
    var decoTimer = null;
    new MutationObserver(function () {
      clearTimeout(decoTimer);
      decoTimer = setTimeout(decorate, 120);
    }).observe(document.documentElement, { childList: true, subtree: true });
  }

  function start() { getCart().then(function (c) { hadCap = c.items.some(isCap); }).catch(function () {}).then(function () { sync(false); }); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
