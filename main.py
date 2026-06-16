
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse, PlainTextResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import configure_databases, get_session
from .models import Member, Transaction
from .routes import menu, orders, transactions
from .schemas import (
    AuthResponse,
    LoginRequest,
    MemberOut,
    RegisterRequest,
    TransactionOut,
)
from .security import generate_token, require_jwt


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_databases()
    yield


app = FastAPI(title="Tea House API", lifespan=lifespan)


@app.get("/", response_class=PlainTextResponse)
def root() -> str:
    return "Tea House API is Live!"


@app.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(
    request: RegisterRequest, session: Session = Depends(get_session)
) -> AuthResponse:
    existing = session.scalar(select(Member).where(Member.phone == request.phone))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Phone number is already registered",
        )

    member = Member(
        id=str(uuid.uuid4()),
        name=request.name,
        email=request.email,
        phone=request.phone,
        points=0,
        tier="Bronze",
    )
    session.add(member)
    session.commit()
    session.refresh(member)

    return AuthResponse(
        token=generate_token(member.id),
        member_id=member.id,
        member=MemberOut.model_validate(member),
    )


@app.post("/login", response_model=AuthResponse)
def login(
    request: LoginRequest, session: Session = Depends(get_session)
) -> AuthResponse:
    member = session.scalar(select(Member).where(Member.phone == request.phone))
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Phone number is not registered",
        )

    return AuthResponse(
        token=generate_token(member.id),
        member_id=member.id,
        member=MemberOut.model_validate(member),
    )


@app.get("/members/{member_id}", response_model=MemberOut)
def get_member(
    member_id: str,
    session: Session = Depends(get_session),
    payload: dict = Depends(require_jwt),
) -> Member:
    if payload.get("id") != member_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own profile",
        )
    member = session.get(Member, member_id)
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return member


@app.get("/members/{member_id}/transactions", response_model=list[TransactionOut])
def get_member_transactions(
    member_id: str,
    session: Session = Depends(get_session),
    payload: dict = Depends(require_jwt),
) -> list[Transaction]:
    # Protected + ownership check: only your own transaction history.
    if payload.get("id") != member_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own transactions",
        )
    if session.get(Member, member_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return list(
        session.scalars(
            select(Transaction).where(Transaction.member_id == member_id)
        )
    )


app.include_router(transactions.router)
app.include_router(menu.router)
app.include_router(orders.router)


@app.get("/kasir", response_class=HTMLResponse)
def kasir_dashboard() -> str:
    return """<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Tea House — Dashboard Kasir</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Segoe UI', sans-serif; background: #f5f0e8; color: #1a1a1a; }

    header {
      background: #1B4D3E;
      color: white;
      padding: 16px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    header h1 { font-size: 18px; letter-spacing: 3px; }
    header span { font-size: 13px; opacity: 0.7; }

    .tabs {
      display: flex;
      gap: 0;
      background: #1B4D3E;
      padding: 0 24px;
    }
    .tab {
      padding: 10px 20px;
      cursor: pointer;
      color: rgba(255,255,255,0.6);
      font-size: 14px;
      border-bottom: 3px solid transparent;
      transition: all 0.2s;
    }
    .tab.active { color: #C5A059; border-bottom-color: #C5A059; }
    .tab:hover { color: white; }

    .container { padding: 24px; max-width: 1000px; margin: 0 auto; }

    .stats {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
      margin-bottom: 24px;
    }
    .stat-card {
      background: white;
      border-radius: 12px;
      padding: 16px 20px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }
    .stat-card .label { font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 1px; }
    .stat-card .value { font-size: 28px; font-weight: 700; color: #1B4D3E; margin-top: 4px; }
    .stat-card.gold .value { color: #C5A059; }

    .section-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 16px;
    }
    .section-header h2 { font-size: 16px; color: #1B4D3E; }
    .refresh-btn {
      background: none;
      border: 1px solid #1B4D3E;
      color: #1B4D3E;
      padding: 6px 14px;
      border-radius: 8px;
      cursor: pointer;
      font-size: 13px;
      transition: all 0.2s;
    }
    .refresh-btn:hover { background: #1B4D3E; color: white; }

    .order-card {
      background: white;
      border-radius: 12px;
      padding: 16px 20px;
      margin-bottom: 12px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.08);
      border-left: 4px solid #e0e0e0;
      transition: box-shadow 0.2s;
    }
    .order-card.pending { border-left-color: #C5A059; }
    .order-card.received { border-left-color: #1B4D3E; }
    .order-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.12); }

    .order-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 10px;
    }
    .order-id { font-size: 12px; color: #888; font-family: monospace; }
    .order-member { font-size: 15px; font-weight: 600; color: #1B4D3E; }
    .order-time { font-size: 12px; color: #aaa; }

    .badge {
      padding: 4px 10px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 600;
    }
    .badge.pending { background: #fff8e1; color: #C5A059; }
    .badge.received { background: #e8f5e9; color: #2e7d32; }

    .items-list { margin: 8px 0; }
    .item-row {
      display: flex;
      justify-content: space-between;
      font-size: 14px;
      color: #444;
      padding: 2px 0;
    }

    .order-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px solid #f0f0f0;
    }
    .total { font-size: 16px; font-weight: 700; color: #1B4D3E; }
    .points-hint { font-size: 12px; color: #888; }

    .approve-btn {
      background: #1B4D3E;
      color: white;
      border: none;
      padding: 8px 20px;
      border-radius: 8px;
      cursor: pointer;
      font-size: 14px;
      font-weight: 600;
      transition: all 0.2s;
    }
    .approve-btn:hover { background: #2e6b5a; }
    .approve-btn:disabled { background: #ccc; cursor: not-allowed; }

    .done-label { color: #2e7d32; font-size: 14px; font-weight: 600; }

    .empty-state {
      text-align: center;
      padding: 48px;
      color: #aaa;
    }
    .empty-state .icon { font-size: 48px; margin-bottom: 12px; }

    .toast {
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: #1B4D3E;
      color: white;
      padding: 12px 20px;
      border-radius: 10px;
      font-size: 14px;
      box-shadow: 0 4px 16px rgba(0,0,0,0.2);
      opacity: 0;
      transform: translateY(10px);
      transition: all 0.3s;
      pointer-events: none;
    }
    .toast.show { opacity: 1; transform: translateY(0); }

    #auto-refresh-bar {
      height: 3px;
      background: #C5A059;
      width: 100%;
      transform-origin: left;
      animation: shrink 10s linear infinite;
    }
    @keyframes shrink { from { transform: scaleX(1); } to { transform: scaleX(0); } }
  </style>
</head>
<body>

<header>
  <h1>☕ TEA HOUSE — KASIR</h1>
  <span id="clock"></span>
</header>
<div id="auto-refresh-bar"></div>

<div class="tabs">
  <div class="tab active" onclick="setFilter('PENDING')">Menunggu</div>
  <div class="tab" onclick="setFilter('RECEIVED')">Selesai</div>
  <div class="tab" onclick="setFilter(null)">Semua</div>
</div>

<div class="container">
  <div class="stats">
    <div class="stat-card">
      <div class="label">Menunggu</div>
      <div class="value" id="stat-pending">—</div>
    </div>
    <div class="stat-card">
      <div class="label">Selesai Hari Ini</div>
      <div class="value" id="stat-received">—</div>
    </div>
    <div class="stat-card gold">
      <div class="label">Total Pendapatan</div>
      <div class="value" id="stat-revenue">—</div>
    </div>
  </div>

  <div class="section-header">
    <h2 id="section-title">Pesanan Menunggu</h2>
    <button class="refresh-btn" onclick="loadOrders()">↻ Refresh</button>
  </div>

  <div id="orders-container"></div>
</div>

<div class="toast" id="toast"></div>

<script>
  let currentFilter = 'PENDING';
  let allOrders = [];

  function setFilter(f) {
    currentFilter = f;
    document.querySelectorAll('.tab').forEach((t, i) => {
      t.classList.toggle('active', [
        'PENDING', 'RECEIVED', null
      ][i] === f);
    });
    const titles = { PENDING: 'Pesanan Menunggu', RECEIVED: 'Pesanan Selesai', null: 'Semua Pesanan' };
    document.getElementById('section-title').textContent = titles[f] ?? 'Semua Pesanan';
    renderOrders();
  }

  function formatRupiah(n) {
    return 'Rp ' + Math.round(n).toLocaleString('id-ID');
  }

  function formatTime(ms) {
    const d = new Date(parseInt(ms));
    return d.toLocaleString('id-ID', { day:'2-digit', month:'short', hour:'2-digit', minute:'2-digit' });
  }

  async function loadOrders() {
    try {
      const res = await fetch('/orders');
      allOrders = await res.json();
      updateStats();
      renderOrders();
    } catch (e) {
      showToast('Gagal memuat pesanan');
    }
  }

  function updateStats() {
    const pending = allOrders.filter(o => o.status === 'PENDING');
    const received = allOrders.filter(o => o.status === 'RECEIVED');
    const revenue = received.reduce((s, o) => s + o.totalAmount, 0);
    document.getElementById('stat-pending').textContent = pending.length;
    document.getElementById('stat-received').textContent = received.length;
    document.getElementById('stat-revenue').textContent = formatRupiah(revenue);
  }

  function renderOrders() {
    const list = currentFilter
      ? allOrders.filter(o => o.status === currentFilter)
      : allOrders;

    const container = document.getElementById('orders-container');
    if (list.length === 0) {
      container.innerHTML = `<div class="empty-state"><div class="icon">🍵</div><div>Tidak ada pesanan</div></div>`;
      return;
    }

    container.innerHTML = list.map(order => {
      const itemsHtml = order.items.map(it =>
        `<div class="item-row">
          <span>${it.menuItemName} × ${it.quantity}</span>
          <span>${formatRupiah(it.unitPrice * it.quantity)}</span>
        </div>`
      ).join('');

      const points = Math.floor(order.totalAmount / 5000);
      const footer = order.status === 'PENDING'
        ? `<button class="approve-btn" onclick="approve('${order.id}', this)">✓ Terima Pesanan</button>`
        : `<span class="done-label">✓ Sudah Diterima</span>`;

      return `
        <div class="order-card ${order.status.toLowerCase()}" id="card-${order.id}">
          <div class="order-header">
            <div>
              <div class="order-id">#${order.id.slice(0,8).toUpperCase()}</div>
              <div class="order-member">Member: ${order.memberId}</div>
              <div class="order-time">${formatTime(order.createdAt)}</div>
            </div>
            <span class="badge ${order.status.toLowerCase()}">${order.status === 'PENDING' ? 'Menunggu' : 'Selesai'}</span>
          </div>
          <div class="items-list">${itemsHtml}</div>
          <div class="order-footer">
            <div>
              <div class="total">${formatRupiah(order.totalAmount)}</div>
              <div class="points-hint">+${points} poin untuk member</div>
            </div>
            ${footer}
          </div>
        </div>`;
    }).join('');
  }

  async function approve(orderId, btn) {
    btn.disabled = true;
    btn.textContent = 'Memproses...';
    try {
      const res = await fetch(`/orders/${orderId}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'RECEIVED' })
      });
      if (!res.ok) throw new Error();
      showToast('Pesanan berhasil diterima! Poin member diperbarui.');
      await loadOrders();
    } catch {
      btn.disabled = false;
      btn.textContent = '✓ Terima Pesanan';
      showToast('Gagal memproses pesanan');
    }
  }

  function showToast(msg) {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 3000);
  }

  function updateClock() {
    document.getElementById('clock').textContent =
      new Date().toLocaleTimeString('id-ID', { hour:'2-digit', minute:'2-digit', second:'2-digit' });
  }

  // Auto-refresh setiap 10 detik
  setInterval(loadOrders, 10000);
  setInterval(updateClock, 1000);

  // Reset animasi progress bar setiap 10 detik
  setInterval(() => {
    const bar = document.getElementById('auto-refresh-bar');
    bar.style.animation = 'none';
    bar.offsetHeight; // reflow
    bar.style.animation = 'shrink 10s linear infinite';
  }, 10000);

  updateClock();
  loadOrders();
</script>
</body>
</html>"""


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
