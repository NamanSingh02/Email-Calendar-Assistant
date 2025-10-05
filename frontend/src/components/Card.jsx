export default function Card({ title, subtitle, right, children }) {
  return (
    <section className="card p-4">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-base font-semibold">{title}</h3>
          {subtitle && <p className="subtle mt-0.5">{subtitle}</p>}
        </div>
        {right}
      </div>
      <div className="mt-3">{children}</div>
    </section>
  );
}
