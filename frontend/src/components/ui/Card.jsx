export default function Card({ title, right, children, className = "" }) {
  return (
    <section className={`card ${className}`.trim()}>
      {(title || right) && (
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
          <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>{title}</h3>
          {right}
        </div>
      )}
      {children}
    </section>
  );
}
