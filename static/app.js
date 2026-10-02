let basket = [];
const $ = (id) => document.getElementById(id);
const api = (url, options = {}) => fetch(url, {headers: {"Content-Type": "application/json"}, ...options}).then(async (response) => {
  const data = await response.json();
  if (!response.ok) throw Error(data.error || "Something went wrong.");
  return data;
});
const esc = (value) => String(value).replace(/[&<>"']/g, (char) => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[char]));
const money = (value) => `₹${Number(value).toFixed(0)}`;

function showView(id, button) {
  document.querySelectorAll(".view").forEach((item) => item.classList.add("hidden"));
  $(id).classList.remove("hidden");
  document.querySelectorAll("nav button").forEach((item) => item.classList.remove("active"));
  if (button) button.classList.add("active");
  if (id === "partner") partnerData();
  if (id === "impact") impact();
}
function toast(message) { const element = $("toast"); element.textContent = message; element.classList.add("show"); setTimeout(() => element.classList.remove("show"), 3600); }

async function loadProducts() {
  try {
    const data = await api(`/api/products?q=${encodeURIComponent($("search").value)}&category=${encodeURIComponent($("category").value)}`);
    $("resultHint").textContent = `${data.length} nearby matches · availability considers stock freshness, store reliability and workload.`;
    $("products").innerHTML = data.map((product) => `<article class="card"><div class="meta">${esc(product.category)} · ${esc(product.store)}, ${esc(product.area)}</div><h3>${esc(product.name)}</h3><div class="meta">${money(product.price)} · ${product.stock} confirmed in stock</div><span class="score ${product.confidence < 70 ? "risk" : ""}">${product.confidence ? `${product.confidence}% fulfilment confidence · ${product.eta} min` : "Unavailable — cannot add"}</span><div class="meta">Stock updated ${product.age_hours < 1 ? "just now" : `${product.age_hours}h ago`}</div><div class="cardFooter"><b>${money(product.price)}</b>${product.confidence ? `<button class="add" onclick="add(${product.id}, '${esc(product.store)}')">Add</button>` : ""}</div></article>`).join("");
  } catch (error) { toast(error.message); }
}

function add(id, store) {
  if (basket.length && basket[0].store !== store) return toast(`For one reliable delivery, finish the ${basket[0].store} basket first.`);
  const item = basket.find((basketItem) => basketItem.id === id);
  if (item) item.quantity += 1;
  else basket.push({id, store, quantity: 1});
  $("basketCount").textContent = basket.reduce((total, basketItem) => total + basketItem.quantity, 0);
  toast(item ? "Quantity increased in your basket." : "Added to your one-store basket.");
}
async function checkout() {
  if (!basket.length) return toast("Add an available product first.");
  try {
    const products = await api("/api/products");
    const items = basket.map((item) => ({...products.find((product) => product.id === item.id), quantity: item.quantity})).filter((item) => item.id);
    if (items.length !== basket.length || items.some((item) => item.stock < item.quantity)) return toast("Your basket changed. Please refresh it.");
    showView("basket");
    $("basketStore").textContent = `Items from ${basket[0].store} · one reliable delivery`;
    $("basketItems").innerHTML = items.map((product) => `<div class="row"><span><b>${esc(product.name)}</b><br><small>Qty ${product.quantity} · ${money(product.price)} each · ${product.stock} confirmed in stock</small></span><button onclick="removeFromBasket(${product.id})">Remove</button></div>`).join("");
    $("basketTotal").textContent = `Total: ${money(items.reduce((sum, product) => sum + product.price * product.quantity, 0))}`;
  } catch (error) { toast(error.message); }
}
function backToShop() { showView("shop", document.querySelector("nav button")); }
function removeFromBasket(id) { basket = basket.filter((item) => item.id !== id); $("basketCount").textContent = basket.reduce((total, item) => total + item.quantity, 0); basket.length ? checkout() : backToShop(); }
async function placeOrder() {
  if (!basket.length) return toast("Add an available product first.");
  try {
    const data = await api("/api/orders", {method: "POST", body: JSON.stringify({product_ids: basket.flatMap((item) => Array(item.quantity).fill(item.id))})});
    toast(`Order #${data.order_id} created · ${data.confidence}% confidence · ETA ${data.eta} min`);
    basket = []; $("basketCount").textContent = 0; backToShop(); loadProducts();
  } catch (error) { toast(error.message); loadProducts(); }
}
async function partnerData() {
  try {
    const data = await api("/api/partner/overview");
    $("inventory").innerHTML = data.products.map((product) => `<div class="row"><div><b>${esc(product.name)}</b><br><small>Demand ${product.demand}/100 · updated ${product.age_hours}h ago</small></div><input id="s${product.id}" aria-label="${esc(product.name)} stock" type="number" min="0" value="${product.stock}"><button onclick="saveStock(${product.id})">Update</button></div>`).join("");
    $("orderList").innerHTML = data.orders.length ? data.orders.map((order) => `<div class="row"><div><b>Order #${order.id} · ${money(order.total)}</b><br><small>${order.items} item(s) · ETA ${order.eta} min</small></div><span class="status">${esc(order.status)}</span><button onclick="nextOrder(${order.id}, '${esc(order.status)}')">${order.status === "Store review" ? "Accept" : "Advance"}</button></div>`).join("") : '<p class="hint">No open orders. Great work.</p>';
    $("watchlist").innerHTML = data.watchlist.map((item) => `<div class="row"><span><b>${esc(item.name)}</b><br><small>Demand ${item.demand}/100</small></span><b>${item.stock} left</b></div>`).join("");
  } catch (error) { toast(error.message); }
}
async function saveStock(id) { try { await api(`/api/inventory/${id}`, {method: "POST", body: JSON.stringify({stock: $(`s${id}`).value})}); toast("Stock updated — shoppers now see the new confidence signal."); partnerData(); loadProducts(); } catch (error) { toast(error.message); } }
async function nextOrder(id, status) { const next = status === "Store review" ? "Accepted" : status === "Accepted" ? "Picking" : status === "Picking" ? "Out for delivery" : "Delivered"; try { await api(`/api/orders/${id}/status`, {method: "POST", body: JSON.stringify({status: next})}); toast(`Order moved to ${next}.`); partnerData(); } catch (error) { toast(error.message); } }
async function impact() { try { const data = await api("/api/summary"); $("metrics").innerHTML = `<div class="metric"><b>${data.fresh}</b>fresh, sellable SKUs</div><div class="metric"><b>${data.risky}</b>SKUs needing attention</div><div class="metric"><b>${data.cancellation_risk}%</b>demo stock-risk share</div><div class="metric"><b>${data.orders}</b>orders tracked</div>`; } catch (error) { toast(error.message); } }
async function resetDemo() { if (!window.confirm("Reset all demo orders and inventory to the original seed data?")) return; try { const data = await api("/api/reset", {method: "POST", body: JSON.stringify({confirm: true})}); basket = []; $("basketCount").textContent = 0; toast(data.message); loadProducts(); impact(); } catch (error) { toast(error.message); } }

loadProducts();
