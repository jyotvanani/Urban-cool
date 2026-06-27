export default function StatCard({ title, value, subtitle, icon: Icon, accent = "brand" }) {
  const accents = {
    brand: "bg-teal-50 text-teal-700",
    blue: "bg-blue-50 text-blue-700",
    orange: "bg-orange-50 text-orange-700",
    red: "bg-red-50 text-red-700",
    green: "bg-green-50 text-green-700",
  };

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500">{title}</p>
          <p className="mt-1 text-2xl font-bold text-slate-800">{value}</p>
          {subtitle && <p className="mt-1 text-xs text-slate-400">{subtitle}</p>}
        </div>
        {Icon && (
          <span
            className={`flex h-10 w-10 items-center justify-center rounded-lg ${
              accents[accent] || accents.brand
            }`}
          >
            <Icon size={20} />
          </span>
        )}
      </div>
    </div>
  );
}
