export default function PageTitle({ title, subtitle }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <h1 style={{ margin: 0, fontSize: 30, fontWeight: 800 }}>{title}</h1>
      {subtitle && <p style={{ margin: "6px 0 0", color: "var(--text-secondary)" }}>{subtitle}</p>}
    </div>
  );
}
