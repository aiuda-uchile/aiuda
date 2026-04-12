export default function MetricCard({ title, value, icon: Icon, tone = "slate" }) {
  const tones = {
    slate: "bg-color-secondary3 text-white",
    blue: "bg-process text-white",
    green: "bg-color-primary3 text-white",
    amber: "bg-color-primary2 text-white",
    rose: "bg-error text-white",
  }

  return (
    <div className="rounded-[1.6rem] border border-white/70 bg-white/85 p-1 shadow-lg shadow-slate-200/60 backdrop-blur">
      <div className={`rounded-[1.2rem] bg-gradient-to-br p-4 ${tones[tone]}`}>
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm opacity-90">{title}</p>
            <p className="mt-1 text-2xl font-semibold tracking-tight">{value}</p>
          </div>
          <div className="rounded-2xl bg-white/15 p-3">
            <Icon className="h-5 w-5" />
          </div>
        </div>
      </div>
    </div>
  )
}