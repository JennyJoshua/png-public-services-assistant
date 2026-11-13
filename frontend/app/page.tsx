import ChatPanel from "./ChatPanel";

export default function Home() {
  return (
    <main className="page-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="PNG Public Services Assistant home">
          <span className="brand-mark" aria-hidden="true">P</span>
          <span>PNG Public Services Assistant</span>
        </a>
        <span className="prototype-label">Early prototype</span>
      </header>

      <section className="hero" aria-labelledby="page-title">
        <p className="eyebrow">PUBLIC INFORMATION · PAPUA NEW GUINEA</p>
        <h1 id="page-title">How can we help you today?</h1>
        <p className="intro">
          Ask a question about public services. Our goal is to explain information
          clearly and show you where it comes from.
        </p>
      </section>

      <ChatPanel />

      <footer className="footer">
        <p>
          This prototype is not a government agency. Always check important
          requirements with the responsible institution.
        </p>
      </footer>
    </main>
  );
}
