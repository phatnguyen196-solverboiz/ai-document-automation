import { Link, NavLink, Outlet } from "react-router-dom";

export function Layout() {
  return (
    <div className="app-frame">
      <aside className="sidebar">
        <Link className="brand" to="/"><span className="brand-icon">FM</span><div><strong>FreightMind</strong><small>Document automation</small></div></Link>
        <nav>
          <NavLink to="/" end>Overview</NavLink>
          <NavLink to="/upload">Upload document</NavLink>
        </nav>
        <div className="sidebar-note"><span>MOCK LLM</span><p>Safe, deterministic demo mode is enabled by default.</p></div>
      </aside>
      <main className="main-column">
        <header className="mobile-header">
          <Link className="brand" to="/"><span className="brand-icon">FM</span><strong>FreightMind</strong></Link>
          <nav><NavLink to="/" end>Documents</NavLink><NavLink to="/upload">Upload</NavLink></nav>
        </header>
        <div className="content"><Outlet /></div>
      </main>
    </div>
  );
}
