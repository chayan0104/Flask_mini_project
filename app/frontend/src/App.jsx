import React, { useCallback, useEffect, useState } from "react";
import "./App.css";

function App() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadOrder = useCallback(async (isRefresh = false) => {
    isRefresh ? setRefreshing(true) : setLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/orders", { cache: "no-store" });
      if (!response.ok) throw new Error(`Orders service returned ${response.status}`);
      setData(await response.json());
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      isRefresh ? setRefreshing(false) : setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadOrder();
  }, [loadOrder]);

  return (
    <main className="app-shell">
      <nav className="topbar" aria-label="Primary navigation">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">M</span>
          <span>Chayan Platform</span>
        </div>
        <div className="status-pill">
          <span className="status-dot" />
          {error ? "Service issue" : "Systems operational"}
        </div>
      </nav>

      <section className="content">
        <header className="hero">
          <div>
            <p className="eyebrow">ORDER OVERVIEW</p>
            <h1>Good to see you.</h1>
            <p className="subtitle">Your latest order and connected customer data.</p>
          </div>
          <button
            className="refresh-button"
            type="button"
            onClick={() => loadOrder(true)}
            disabled={refreshing || loading}
          >
            <span className={refreshing ? "refresh-icon spinning" : "refresh-icon"} aria-hidden="true">↻</span>
            {refreshing ? "Refreshing…" : "Refresh"}
          </button>
        </header>

        {loading ? (
          <section className="card loading-card" aria-live="polite">
            <div className="skeleton skeleton-title" />
            <div className="skeleton skeleton-line" />
            <div className="skeleton skeleton-line short" />
          </section>
        ) : error ? (
          <section className="card error-card" role="alert">
            <div className="error-icon" aria-hidden="true">!</div>
            <div>
              <h2>Couldn’t load the order</h2>
              <p>{error}</p>
            </div>
            <button type="button" onClick={() => loadOrder(true)}>Try again</button>
          </section>
        ) : (
          <>
            <section className="order-card card">
              <div className="card-heading">
                <div>
                  <p className="card-label">LATEST ORDER</p>
                  <h2>Order #{data.order_id}</h2>
                </div>
                <span className="order-status">{data.status}</span>
              </div>
              <div className="divider" />
              <div className="details-grid">
                <div>
                  <p className="detail-label">Order ID</p>
                  <p className="detail-value">#{data.order_id}</p>
                </div>
                <div>
                  <p className="detail-label">Status</p>
                  <p className="detail-value capitalize">{data.status}</p>
                </div>
                <div>
                  <p className="detail-label">Customers loaded</p>
                  <p className="detail-value">{data.user_data?.users?.length ?? 0}</p>
                </div>
              </div>
            </section>

            <section className="card users-card">
              <div className="card-heading">
                <div>
                  <p className="card-label">CONNECTED USERS</p>
                  <h2>Customer directory</h2>
                </div>
              </div>
              <div className="user-list">
                {(data.user_data?.users || []).map((name, index) => (
                  <article className="user-row" key={name}>
                    <div className="avatar">{name.charAt(0).toUpperCase()}</div>
                    <div>
                      <p className="user-name">{name}</p>
                      <p className="user-meta">Customer {String(index + 1).padStart(2, "0")}</p>
                    </div>
                    <span className="active-dot" title="Active" />
                  </article>
                ))}
              </div>
            </section>
          </>
        )}
      </section>
    </main>
  );
}
export default App;