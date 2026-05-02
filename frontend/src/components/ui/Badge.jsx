const variants = {
  success: { background: "rgba(69,223,164,0.16)", color: "#45dfa4" },
  warning: { background: "rgba(251,191,36,0.16)", color: "#fbbf24" },
  danger: { background: "rgba(220,38,38,0.16)", color: "#ffb4ab" },
  info: { background: "rgba(59,130,246,0.16)", color: "#b4c5ff" },
};

export default function Badge({ children, variant = "info" }) {
  const style = variants[variant] || variants.info;
  return (
    <span className="badge" style={style}>
      {children}
    </span>
  );
}
