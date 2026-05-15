export default function Skeleton({ width = "100%", height = 20, count = 1, style = {} }) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          style={{
            width,
            height,
            borderRadius: 6,
            background: "linear-gradient(90deg, var(--surface-high) 25%, var(--surface-highest) 50%, var(--surface-high) 75%)",
            backgroundSize: "200% 100%",
            animation: "shimmer 1.5s infinite",
            marginBottom: i < count - 1 ? 8 : 0,
            ...style
          }}
        />
      ))}
    </>
  );
}
