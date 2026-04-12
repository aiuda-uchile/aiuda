export default function ProgressCircle({ value = 0, size = 200, strokeWidth = 10 }) {
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius

  const progress = Math.min(Math.max(value, 0), 100)
  const offset = circumference - (progress / 100) * circumference
  let color = "stroke-primary-3"
  if (progress < 40) color = "stroke-error"
  else if (progress <= 60) color = "stroke-process-2"

  return (
    <div className="flex items-center justify-center">
      <svg width={size} height={size} className="rotate-[-90deg]">

        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
          className="stroke-slate-200"
          fill="transparent"
        />

        {/* Progreso */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
          className={`${color} transition-all duration-500`}
          fill="transparent"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
        />
      </svg>

      {/* Texto porcentaje*/}
      <div className="absolute text-center">
        <span className="text-3xl font-bold">
          {progress}%
        </span>
      </div>
    </div>
  )
}