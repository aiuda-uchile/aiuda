import { useEffect, useMemo, useRef, useState } from "react"
import {
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  Clock3,
  Cpu,
  Download,
  FileText,
  Filter,
  Loader2,
  Mail,
  Mic,
  Upload,
  Video,
  Search,
  Captions,
  ListMinus,
  Languages,
  PersonStanding,
  PaintBucket,
  CaseSensitive,
  CirclePlay,
  CirclePlus,
  Presentation,
  Volume2,
  UserCog,
  Menu,
  X
} from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { header } from "framer-motion/client"

import { useI18n } from "./i18n/i18n"
import MetricCard from "./components/scripts/MetricCard"
import Terms from "./components/scripts/Terms"

const BASE_URL = import.meta.env.BASE_URL || "/"

function getPublicAssetUrl(path) {
  return `${BASE_URL}${String(path).replace(/^\/+/, "")}`
}

const TARGET_LANGS = [
  { code: "es", label: "Español", icon: "🇪🇸" },
  { code: "en", label: "Inglés", icon: "🇬🇧" },
  { code: "pt", label: "Portugués", icon: "🇧🇷" },
  { code: "gl", label: "Gallego", icon: getPublicAssetUrl("galicia-icon.png") },
]

const LANGUAGE_META = {
  original: { label: "Original", icon: "📄" },
  es: { label: "Español", icon: "🇪🇸" },
  en: { label: "Inglés", icon: "🇬🇧" },
  pt: { label: "Portugués", icon: "🇧🇷" },
  gl: { label: "Gallego", icon: getPublicAssetUrl("galicia-icon.png") },
}

const AIUDA_LOGOS_SRC = getPublicAssetUrl("assets/iconos/1x/aiuda-logo02.png")
const AIUDA_NEGATIVE_LOGOS_SRC = getPublicAssetUrl("assets/iconos/1x/aiuda-logo02-negativo.png")
const TASKS_PER_PAGE = 6
const INITIAL_FORM = {
  mode: "multimedia",
  mediaType: "video",
  email: "",
  notes: "",
  options: {
    subtitles: true,
    transcription: true,
    translation: true,
    extract_audio: true,
    accessibility: true,
    color_blindness: true,
    small_fonts: true,
    long_texts: true,
    writing_issues: true,
    ocr: false,
    notify_by_email: true,
    source_lang_mode: "auto",
    source_lang: "",
    target_langs: ["es", "en", "pt", "gl"],
  },
}

function formatDate(value) {
  if (!value) return "-"
  try {
    return new Date(value).toLocaleString()
  } catch {
    return value
  }
}

function getTaskTypeLabel(taskType) {
  if (taskType === "audio") return "Audio"
  if (taskType === "video") return "video"
  if (taskType === "documents") return "Documentos"
  return taskType || "Tarea"
}

function getTaskIcon(taskType) {
  if (taskType === "audio") return Mic
  if (taskType === "video") return Video
  if (taskType === "documents") return FileText
  return FileText
}

function getStatusConfig(status) {
  switch (status) {
    case "queued":
      return {
        label: "En cola",
        badge: "border-amber-200 bg-amber-50 text-amber-700",
        bar: "bg-amber-500",
        icon: Clock3,
      }
    case "processing":
      return {
        label: "Procesando",
        badge: "border-sky-200 bg-process text-white",
        bar: "bg-process",
        icon: Loader2,
      }
    case "finished":
      return {
        label: "Finalizada",
        badge: "border-primary3 bg-color-primary3 text-white text-sm h-7",
        bar: "bg-color-primary3",
        icon: CheckCircle2,
      }
    case "error":
      return {
        label: "Con error",
        badge: "border-red-200 bg-error text-white",
        bar: "bg-error",
        icon: AlertTriangle,
      }
    default:
      return {
        label: status || "Desconocido",
        badge: "border-slate-200 bg-slate-50 text-slate-700",
        bar: "bg-slate-500",
        icon: Clock3,
      }
  }
}

function getMainDateByStatus(task) {
  if (!task) {
    return { label: "Fecha", value: null }
  }

  switch (task.status) {
    case "finished":
      return {
        label: "Finalizada",
        value: task.finished_at || task.updated_at,
      }
    case "processing":
      return {
        label: "Iniciada",
        value: task.started_at || task.updated_at || task.created_at,
      }
    case "queued":
      return {
        label: "Recibida",
        value: task.created_at,
      }
    case "error":
      return {
        label: "Error",
        value: task.finished_at || task.updated_at || task.created_at,
      }
    default:
      return {
        label: "Fecha",
        value: task.updated_at || task.created_at,
      }
  }
}

function getNotificationState(task) {
  if (task?.notification_status) return task.notification_status
  if (task?.notified === true) return "sent"
  if (task?.notification_sent === true) return "sent"
  if (task?.notified_at) return "sent"
  if (task?.email) return "pending"
  return "disabled"
}

function getAcceptForForm(mode, mediaType) {
  if (mode === "multimedia") {
    if (mediaType === "video") return ".mp4,.mov,.avi,.wmv,.mkv,.webm"
    // Audio: .doc y .docx reservados para el futuro
    return ".mp3,.wav,.m4a,.ogg"
  }
  // Documentos: .doc y .docx comentados, listos para habilitar en el futuro
  // return ".pdf,.ppt,.pptx,.doc,.docx"
  return ".pdf,.ppt,.pptx"
}

function buildPayload(form) {
  let task_type = "documents"

  if (form.mode === "multimedia") {
    task_type = form.mediaType === "video" ? "video" : "audio"
  }

  return {
    task_type,
    email: form.email.trim(),
    notes: form.notes.trim(),
    notify_email: String(!!form.options.notify_by_email),
    translate: String(!!form.options.translation),
    accessibility: String(!!form.options.accessibility),
    ocr: String(!!form.options.ocr),
    source_lang:
      form.options.source_lang_mode === "manual"
        ? form.options.source_lang.trim() || "auto"
        : "auto",
    target_langs: form.options.target_langs.join(","),
  }
}

function isTaskActive(task) {
  return task.status === "queued" || task.status === "processing"
}

function getJsonPreviewItems(outputs = []) {
  const order = ["es", "en", "gl", "pt"]
  const labels = {
    es: "ES",
    en: "EN",
    gl: "GL",
    pt: "PT",
  }
  const icons = {
    es: "🇪🇸",
    en: "🇬🇧",
    gl: getPublicAssetUrl("galicia-icon.png"),
    pt: "🇵🇹",
  }

  return outputs
    .map((filename) => {
      const match = String(filename).match(/\.(es|en|gl|pt)\.json$/i)
      if (!match) return null

      const key = match[1].toLowerCase()
      return {
        key,
        label: labels[key],
        icon: icons[key] ?? null,
        filename,
      }
    })
    .filter(Boolean)
    .sort((a, b) => order.indexOf(a.key) - order.indexOf(b.key))
}

function getPreviewCacheKey(taskId, filename) {
  return `${taskId}:${filename}`
}

function formatSeconds(value) {
  const totalSeconds = Math.max(0, Math.floor(Number(value) || 0))
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60

  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`
}

function findVariantOutput(outputs = [], key, extension) {
  const regex = new RegExp(`\\.${key}\\.${extension}$`, "i")
  return outputs.find((filename) => regex.test(String(filename))) || null
}

function findSubtitledVideoOutput(outputs = [], key) {
  if (!key) return null
  const regex = new RegExp(`\\.${key}\\.subtitled\\.mp4$`, "i")
  return outputs.find((filename) => regex.test(String(filename))) || null
}

function PipelineMini({ task }) {
  const status = task?.status
  const steps = [
    { key: "uploaded", label: "Enviado" },
    { key: "queued", label: "En cola" },
    { key: "engine", label: "En proceso" },
    { key: "ready", label: "Finalizado" },
    { key: "notified", label: "Notificado" },
  ]

  function stepActive(stepKey) {
    if (!task) return false

    if (stepKey === "uploaded") return true
    if (stepKey === "queued")
      return ["queued", "processing", "finished", "error"].includes(status)
    if (stepKey === "engine")
      return ["processing", "finished", "error"].includes(status)
    if (stepKey === "ready") return ["finished"].includes(status)
    if (stepKey === "notified") return getNotificationState(task) === "sent"

    return false
  }

  const activeConnectorCount = Math.max(
    0,
    steps.filter((step) => stepActive(step.key)).length - 1,
  )

  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <div className="relative pt-1">
        <div className="pointer-events-none absolute left-[10%] right-[10%] top-5 hidden h-1 rounded-full bg-slate-200 md:block" />
        <div
          className="pointer-events-none absolute left-[10%] top-5 hidden h-1 rounded-full bg-color-primary3 md:block"
          style={{
            width: `calc(80% * ${activeConnectorCount / Math.max(steps.length - 1, 1)
              })`,
          }}
        />

        <div className="grid grid-cols-5 gap-2">
          {steps.map((step, idx) => {
            const active = stepActive(step.key)
            return (
              <div
                key={step.key}
                className="flex flex-col items-center gap-2 text-center"
              >
                <div
                  className={`relative z-10 flex h-11 w-11 items-center justify-center rounded-full border text-base font-semibold ${active
                      ? "border-primary3 bg-color-primary3 text-white"
                      : "border-slate-300 bg-white"
                    }`}
                >
                  {idx + 1}
                </div>
                <p className="text-center text-base leading-4 mt-2">
                  {step.label}
                </p>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
function getColorClassByPercentage(value) {
  if (value < 40) return "bg-error"
  if (value <= 60) return "bg-process"
  return "bg-color-primary3"
}
function getDocumentPreviewData(raw) {
  if (!raw || typeof raw !== "object") return null

  const summary = raw.summary && typeof raw.summary === "object" ? raw.summary : null
  const issues = Array.isArray(raw.issues) ? raw.issues : []
  const recommendations = Array.isArray(raw.recommendations)
    ? raw.recommendations
    : []
  const visualMetrics =
    raw.visual_metrics && typeof raw.visual_metrics === "object"
      ? raw.visual_metrics
      : null

  if (!summary && issues.length === 0 && recommendations.length === 0 && !visualMetrics) return null

  return { summary, issues, recommendations, visualMetrics }
}

const DOCUMENT_CATEGORY_META = {
  color_blindness: {
    label: "Daltonismo/color",
    description: "Uso del color y contraste",
  },
  small_fonts: {
    label: "Tamaño de letra",
    description: "Legibilidad tipográfica",
  },
  long_texts: {
    label: "Textos largos",
    description: "Densidad del contenido",
  },
}

const DOCUMENT_CATEGORY_ALIASES = {
  color_blindness: ["color_blindness", "color_contrast", "cvd_risk"],
  small_fonts: ["small_fonts"],
  long_texts: ["long_texts", "dense_text"],
}

function getDocumentScoreLabel(score) {
  if (score === null || score === undefined) return "Sin datos"
  if (score >= 90) return "Muy bien"
  if (score >= 75) return "Bien"
  if (score >= 55) return "Atención"
  return "Revisar"
}

function getDocumentScoreTone(score) {
  if (score === null || score === undefined) {
    return {
      badge: "border-slate-200 bg-slate-50 text-slate-600",
      bar: "bg-slate-300",
    }
  }
  if (score >= 90) {
    return {
      badge: "border-emerald-200 bg-emerald-50 text-emerald-700",
      bar: "bg-emerald-500",
    }
  }
  if (score >= 75) {
    return {
      badge: "border-sky-200 bg-sky-50 text-sky-700",
      bar: "bg-sky-500",
    }
  }
  if (score >= 55) {
    return {
      badge: "border-amber-200 bg-amber-50 text-amber-700",
      bar: "bg-amber-500",
    }
  }
  return {
    badge: "border-red-200 bg-red-50 text-red-700",
    bar: "bg-red-500",
  }
}

function clampDocumentStateIndex(index) {
  return Math.max(0, Math.min(3, index))
}

function getDocumentStateIndex(label) {
  const order = ["Revisar", "Atención", "Bien", "Muy bien"]
  const idx = order.indexOf(label)
  return idx === -1 ? 0 : idx
}

function downgradeDocumentState(label, steps = 1) {
  if (!label || label === "Sin datos") return label
  const order = ["Revisar", "Atención", "Bien", "Muy bien"]
  const nextIndex = clampDocumentStateIndex(getDocumentStateIndex(label) - steps)
  return order[nextIndex]
}

function getPenaltyFromSeverity(severityCode) {
  if (severityCode === "high") return 25
  if (severityCode === "medium") return 12
  return 6
}

function formatMetricValue(value, digits = 2) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return null
  return numeric.toFixed(digits)
}

function singularOrPlural(value, singular, plural) {
  return value === 1 ? singular : plural
}

function extractFirstPointSize(issues = []) {
  for (const issue of issues) {
    const text = `${issue?.description || ""} ${issue?.excerpt || ""}`
    const match = text.match(/(\d+(?:[.,]\d+)?)\s*pt/i)
    if (match) return match[1].replace(",", ".")
  }
  return null
}

function getWorstFigureSample(visualMetrics) {
  const rows = Array.isArray(visualMetrics?.figure_metric_samples)
    ? visualMetrics.figure_metric_samples
    : []

  if (rows.length === 0) return null

  return [...rows]
    .filter((row) => row && row.worst_cvd_ratio !== null && row.worst_cvd_ratio !== undefined)
    .sort((a, b) => Number(a?.worst_cvd_ratio ?? 1) - Number(b?.worst_cvd_ratio ?? 1))[0] || null
}

function getDocumentCategoryStateLabel(
  score,
  { criticalCount = 0, warningCount = 0, hasAttention = false } = {},
) {
  if (score === null || score === undefined) return "Sin datos"

  let label = getDocumentScoreLabel(score)

  if (criticalCount >= 2) {
    label = downgradeDocumentState(label, 2)
  } else if (criticalCount >= 1) {
    label = downgradeDocumentState(label, 1)
  } else if ((warningCount > 0 || hasAttention) && label === "Muy bien") {
    label = "Bien"
  }

  return label
}

function buildDocumentCategoryDetail(key, matchedIssues, visualMetrics) {
  const figureSummary = visualMetrics?.figure_metrics_summary || {}
  const worstFigureSample = getWorstFigureSample(visualMetrics)
  const criticalCount = matchedIssues.filter(
    (issue) => issue?.severity_code === "high",
  ).length
  const warningCount = matchedIssues.filter(
    (issue) => issue?.severity_code && issue?.severity_code !== "high",
  ).length

  if (key === "color_blindness") {
    const issueCount = matchedIssues.length
    const minCvdRatio = Number(figureSummary?.min_cvd_ratio)
    const hasMinCvdRatio = Number.isFinite(minCvdRatio)
    const hasAttention = issueCount === 0 && hasMinCvdRatio && minCvdRatio < 0.92
    const worstMode =
      worstFigureSample?.worst_cvd_type ||
      worstFigureSample?.cvd_type ||
      worstFigureSample?.worst_cvd ||
      null

    if (issueCount > 0) {
      const issueLabel = criticalCount > 0 ? "incid. crítica" : "incid."
      const issueLabelPlural = criticalCount > 0 ? "incid. críticas" : "incid."
      if (hasMinCvdRatio && worstMode) {
        return {
          detail: `${issueCount} ${singularOrPlural(issueCount, issueLabel, issueLabelPlural)} · Peor score CVD: ${formatMetricValue(minCvdRatio, 2)} · ${worstMode}`,
          hasAttention: false,
          criticalCount,
          warningCount,
        }
      }

      return {
        detail: `${issueCount} ${singularOrPlural(issueCount, issueLabel, issueLabelPlural)} · Revisar figuras dependientes del color`,
        hasAttention: false,
        criticalCount,
        warningCount,
      }
    }

    if (hasAttention) {
      const detail = hasMinCvdRatio
        ? worstMode
          ? `Sin incidencias críticas · Peor score CVD: ${formatMetricValue(minCvdRatio, 2)} · ${worstMode}`
          : `Sin incidencias críticas · Peor score CVD: ${formatMetricValue(minCvdRatio, 2)}`
        : "Sin incidencias críticas · 1 figura a vigilar"

      return {
        detail,
        hasAttention: true,
        criticalCount,
        warningCount,
      }
    }

    return {
      detail: "Sin riesgos CVD relevantes",
      hasAttention: false,
      criticalCount,
      warningCount,
    }
  }

  if (key === "small_fonts") {
    const pointSize = extractFirstPointSize(matchedIssues)
    const issueCount = matchedIssues.length

    if (issueCount > 0) {
      return {
        detail: pointSize
          ? `${issueCount} ${singularOrPlural(issueCount, "incid.", "incid.")} · ejemplo detectado: ${pointSize} pt`
          : `${issueCount} ${singularOrPlural(issueCount, "incid.", "incid.")} · revisar legibilidad tipográfica`,
        hasAttention: false,
        criticalCount,
        warningCount,
      }
    }

    return {
      detail: "Sin alertas relevantes de tamaño",
      hasAttention: false,
      criticalCount,
      warningCount,
    }
  }

  if (key === "long_texts") {
    const issueCount = matchedIssues.length

    if (issueCount > 0) {
      return {
        detail: `${issueCount} ${singularOrPlural(issueCount, "sección con exceso de texto", "secciones con exceso de texto")}`,
        hasAttention: false,
        criticalCount,
        warningCount,
      }
    }

    return {
      detail: "Sin sobrecarga textual relevante",
      hasAttention: false,
      criticalCount,
      warningCount,
    }
  }

  return {
    detail: matchedIssues.length > 0 ? `${matchedIssues.length} incid.` : "Sin alertas relevantes",
    hasAttention: false,
    criticalCount,
    warningCount,
  }
}

function buildGlobalDocumentSummary(categorySummaries) {
  if (!Array.isArray(categorySummaries) || categorySummaries.length === 0) {
    return "Sin datos suficientes para resumir el análisis."
  }

  const issueCategory = [...categorySummaries]
    .filter((item) => item.count > 0)
    .sort((a, b) => a.score - b.score || b.count - a.count)[0]

  if (issueCategory) {
    return `Principal mejora pendiente: ${issueCategory.label.toLowerCase()}`
  }

  const attentionCategory = categorySummaries.find((item) => item.hasAttention)
  if (attentionCategory?.key === "color_blindness") {
    return "Documento correcto, con alguna figura a vigilar por color."
  }

  return "Sin alertas visuales relevantes en esta revisión."
}

function buildDocumentCategorySummaries(preview) {
  const issues = Array.isArray(preview?.issues) ? preview.issues : []
  const visualMetrics = preview?.visualMetrics || null

  return Object.entries(DOCUMENT_CATEGORY_META).map(([key, meta]) => {
    const aliases = DOCUMENT_CATEGORY_ALIASES[key] || [key]
    const matchedIssues = issues.filter((issue) =>
      aliases.includes(issue?.category_code),
    )

    const penalty = matchedIssues.reduce(
      (sum, issue) => sum + getPenaltyFromSeverity(issue?.severity_code),
      0,
    )

    const detailMeta = buildDocumentCategoryDetail(key, matchedIssues, visualMetrics)
    const attentionPenalty = detailMeta.hasAttention ? 10 : 0
    const score = Math.max(0, 100 - penalty - attentionPenalty)

    return {
      key,
      ...meta,
      score,
      count: matchedIssues.length,
      tone: getDocumentScoreTone(score),
      labelScore: getDocumentCategoryStateLabel(score, {
        criticalCount: detailMeta.criticalCount,
        warningCount: detailMeta.warningCount,
        hasAttention: detailMeta.hasAttention,
      }),
      detail: detailMeta.detail,
      hasAttention: detailMeta.hasAttention,
      criticalCount: detailMeta.criticalCount,
      warningCount: detailMeta.warningCount,
    }
  })
}

function buildGlobalDocumentScore(categorySummaries) {
  const valid = categorySummaries.filter(
    (item) => typeof item.score === "number",
  )

  if (valid.length === 0) return null

  const avg =
    valid.reduce((sum, item) => sum + item.score, 0) / valid.length

  return Math.round(avg)
}

export default function App() {
  const [form, setForm] = useState(INITIAL_FORM)
  const [selectedFile, setSelectedFile] = useState(null)
  const [isDraggingFile, setIsDraggingFile] = useState(false)
  const [tasks, setTasks] = useState([])
  const [selectedTaskId, setSelectedTaskId] = useState(null)
  const [filter, setFilter] = useState("all")
  const [searchId, setSearchId] = useState("")
  const [currentPage, setCurrentPage] = useState(1)
  const [loadingTasks, setLoadingTasks] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [uiError, setUiError] = useState("")
  const [errors, setErrors] = useState({})
  const [success, setSuccess] = useState(false)
  const [logsByTask, setLogsByTask] = useState({})
  const [loadingLogId, setLoadingLogId] = useState(null)
  const [previewJsonByFile, setPreviewJsonByFile] = useState({})
  const [loadingJsonPreviewKey, setLoadingJsonPreviewKey] = useState(null)
  const [selectedJsonTab, setSelectedJsonTab] = useState("original")
  const audioPlayerRef = useRef(null)
  const [currentAudioTime, setCurrentAudioTime] = useState(0)
  const segmentRefs = useRef({})
  const logScrollRef = useRef(null)
  const [showLogByTask, setShowLogByTask] = useState({})
  const { t, lang,changeLanguage } = useI18n()
  const languagesNav = ["es","pt","gl"]
  const [profile, setProfile] = useState("teacher")
  const [menuOpen, setMenuOpen] = useState(false)
  const [acceptedTerms, setAcceptedTerms] = useState(false)
  const [showTerms, setShowTerms] = useState(false)

  useEffect(() => {
    if (window.location.pathname === "/aiuda/admin") {
      setProfile("technical")
    }
  }, [])
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const q = params.get("q")

    if (q) {
      setSearchId(q)
      setTimeout(() => {
      const el = document.getElementById("buscar")
      if (el) {
        el.scrollIntoView({ behavior: "smooth" })
      }
    }, 100)
    }
  }, [])
  
  
  function toggleProfile() {
    setProfile((prev) =>
      prev === "teacher" ? "technical" : "teacher"
    )
  }

  async function fetchTasks(silent = false) {
    if (!silent) setLoadingTasks(true)
    try {
      const response = await fetch("/api/tasks")
      if (!response.ok) {
        throw new Error(`No se pudieron cargar las tareas (${response.status})`)
      }
      const data = await response.json()
      const nextTasks = Array.isArray(data.tasks) ? data.tasks : []
      setTasks(nextTasks)

      setSelectedTaskId((prevSelectedTaskId) => {
        if (nextTasks.length === 0) return null

        const exists = nextTasks.some((t) => t.id === prevSelectedTaskId)
        if (!prevSelectedTaskId || !exists) {
          return nextTasks[0].id
        }

        return prevSelectedTaskId
      })

      setUiError("")
    } catch (error) {
      setUiError(error.message || "Error cargando tareas.")
    } finally {
      if (!silent) setLoadingTasks(false)
    }
  }

  function handleTaskCardClick(task) {
    setSelectedTaskId(task.id)

    if (task.status === "error") {
      setShowLogByTask((prev) => ({
        ...prev,
        [task.id]: true,
      }))

      if (logsByTask[task.id] === undefined) {
        loadLog(task.id)
      }
    }
  }

  useEffect(() => {
    fetchTasks()
    const interval = setInterval(() => fetchTasks(true), 3000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    setCurrentPage(1)
  }, [filter, searchId])



  function setOption(key, value) {
    setForm((prev) => ({
      ...prev,
      options: {
        ...prev.options,
        [key]: value,
      },
    }))
  }

  function handleModeChange(mode) {
    setForm((prev) => ({
      ...prev,
      mode,
      mediaType: mode === "multimedia" ? "audio" : "video",
      options: {
        ...prev.options,
        accessibility: mode === "documental",
        subtitles: false,
        transcription: mode === "multimedia",
        extract_audio: false,
      },
    }))
  }

  function handleMediaTypeChange(value) {
    setForm((prev) => ({
      ...prev,
      mediaType: value,
      options: {
        ...prev.options,
        subtitles: value === "video",
        transcription: true,
        extract_audio: value === "video",
        accessibility: false,
      },
    }))
  }

  function toggleTargetLang(code, checked) {
    setForm((prev) => {
      const current = new Set(prev.options.target_langs)
      if (checked) current.add(code)
      else current.delete(code)

      return {
        ...prev,
        options: {
          ...prev.options,
          target_langs: Array.from(current),
        },
      }
    })
  }

  async function submitTask(event) {
    event.preventDefault()
    let newErrors = {}
    setSuccess(false)
    //validar email
    if (!form.email.trim()) {
      newErrors.email = "El email es obligatorio."
    } else {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      if (!emailRegex.test(form.email)) {
        newErrors.email = "Introduce un email válido."
      }
    }
    if (!selectedFile) {
      newErrors.file = "Debes subir un archivo."
    } else if (selectedFile.size === 0) {
      newErrors.file = "El archivo está vacío."
    }

    if (form.options.translation && form.options.target_langs.length === 0) {
      setUiError("Selecciona al menos un idioma destino.")
      return
    }

    if (
      form.options.source_lang_mode === "manual" &&
      !form.options.source_lang.trim()
    ) {
      setUiError("Indica el idioma origen o usa detección automática.")
      return
    }
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors)
      setSuccess(false)
      return
    }
    //limpiar errores
    setErrors({})
    setSuccess(false)
    setSubmitting(true)


    try {
      const payload = buildPayload(form)
      const formData = new FormData()
      formData.append("file", selectedFile)
      formData.append("task_type", payload.task_type)
      formData.append("email", payload.email || "")
      formData.append("notes", payload.notes || "")
      formData.append("notify_email", payload.notify_email)
      formData.append("translate", payload.translate)
      formData.append("accessibility", payload.accessibility)
      formData.append("ocr", payload.ocr)
      formData.append("source_lang", payload.source_lang)
      formData.append("target_langs", payload.target_langs)

      const response = await fetch("http://127.0.0.1:8000/api/tasks", {
        method: "POST",
        body: formData,
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          data?.detail || `Error creando tarea (${response.status})`,
        )
      }

      await fetchTasks()
      setSelectedFile(null)
      setForm(INITIAL_FORM)
      setSelectedFile(null)
      setAcceptedTerms(false)

      const fileInput = document.getElementById("aluda-file-input")
      if (fileInput) fileInput.value = ""

      setSuccess(true)
    } catch (error) {
      setUiError(error.message || "Error creando la tarea.")
      setErrors({ general: error.message })
      /*Eliminar esto después*/
      setSuccess(true)
      setForm(INITIAL_FORM)
      setSelectedFile(null)
      setAcceptedTerms(false)
      /*Hasta acá*/
    } finally {
      setSubmitting(false)
    }
  }

  function downloadGroup(taskId, files) {
    files.forEach((filename, index) => {
      window.setTimeout(() => {
        const link = document.createElement("a")
        link.href = `/api/tasks/${taskId}/download/${encodeURIComponent(
          filename,
        )}`
        link.download = filename
        document.body.appendChild(link)
        link.click()
        link.remove()
      }, index * 200)
    })
  }

  async function fetchLogText(taskId) {
    const response = await fetch(`/api/tasks/${taskId}/log`)

    if (!response.ok) {
      throw new Error(`No se pudo cargar la información del procesamiento (${response.status})`)
    }

    return await response.text()
  }

  async function loadLog(taskId) {
    try {
      setLoadingLogId(taskId)

      const logText = await fetchLogText(taskId)

      setLogsByTask((prev) => ({
        ...prev,
        [taskId]: logText || "Registro vacío.",
      }))
    } catch (error) {
      setLogsByTask((prev) => ({
        ...prev,
        [taskId]: `Error cargando la información del procesamiento: ${error.message || "desconocido"
          }`,
      }))
    } finally {
      setLoadingLogId(null)
    }
  }

  async function refreshLogSilently(taskId) {
    try {
      const logText = await fetchLogText(taskId)

      setLogsByTask((prev) => ({
        ...prev,
        [taskId]: logText || "Registro vacío.",
      }))
    } catch (error) {
      setLogsByTask((prev) => ({
        ...prev,
        [taskId]: `Error cargando la información del procesamiento: ${error.message || "desconocido"
          }`,
      }))
    }
  }

  async function downloadLog(taskId) {
    try {
      setLoadingLogId(taskId)

      const cachedLog = logsByTask[taskId]
      const logText = cachedLog !== undefined ? cachedLog : await fetchLogText(taskId)

      if (cachedLog === undefined) {
        setLogsByTask((prev) => ({
          ...prev,
          [taskId]: logText || "Registro vacío.",
        }))
      }

      const blob = new Blob([logText || "Registro vacío."], {
        type: "text/plain;charset=utf-8",
      })

      const url = URL.createObjectURL(blob)
      const link = document.createElement("a")
      link.href = url
      link.download = `aluda-procesamiento-${taskId}.log`
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
    } catch (error) {
      setUiError(
        error.message || "No se pudo descargar la información del procesamiento.",
      )
    } finally {
      setLoadingLogId(null)
    }
  }

  async function toggleLog(taskId) {
    const isOpen = !!showLogByTask[taskId]

    if (!isOpen && logsByTask[taskId] === undefined) {
      await loadLog(taskId)
    }

    setShowLogByTask((prev) => ({
      ...prev,
      [taskId]: !prev[taskId],
    }))
  }

  async function loadJsonPreview(taskId, filename) {
    const cacheKey = getPreviewCacheKey(taskId, filename)

    try {
      setLoadingJsonPreviewKey(cacheKey)

      const response = await fetch(
        `/api/tasks/${taskId}/download/${encodeURIComponent(filename)}`,
      )

      if (!response.ok) {
        throw new Error(`No se pudo cargar la vista previa (${response.status})`)
      }

      const data = await response.json()

      setPreviewJsonByFile((prev) => ({
        ...prev,
        [cacheKey]: data,
      }))
    } catch (error) {
      setPreviewJsonByFile((prev) => ({
        ...prev,
        [cacheKey]: {
          error: `Error cargando vista previa: ${error.message || "desconocido"}`,
          segments: [],
        },
      }))
    } finally {
      setLoadingJsonPreviewKey(null)
    }
  }

  const counts = useMemo(() => {
    const notified = tasks.filter((t) => getNotificationState(t) === "sent").length

    return {
      queued: tasks.filter((t) => t.status === "queued").length,
      processing: tasks.filter((t) => t.status === "processing").length,
      finished: tasks.filter((t) => t.status === "finished").length,
      error: tasks.filter((t) => t.status === "error").length,
      notified,
    }
  }, [tasks])

  const filteredTasks = useMemo(() => {
    let nextTasks

    switch (filter) {
      case "active":
        nextTasks = tasks.filter(isTaskActive)
        break
      case "finished":
        nextTasks = tasks.filter((t) => t.status === "finished")
        break
      case "error":
        nextTasks = tasks.filter((t) => t.status === "error")
        break
      default:
        nextTasks = tasks
        break
    }

    const normalizedSearchId = searchId.trim().toLowerCase()
    if (!normalizedSearchId) return nextTasks

    return nextTasks.filter((task) =>
      String(task.id || "").toLowerCase().includes(normalizedSearchId),
    )
  }, [tasks, filter, searchId])

  const totalPages = Math.max(
    1,
    Math.ceil(filteredTasks.length / TASKS_PER_PAGE),
  )

  useEffect(() => {
    setCurrentPage((prev) => Math.min(prev, totalPages))
  }, [totalPages])

  const paginatedTasks = useMemo(() => {
    const start = (currentPage - 1) * TASKS_PER_PAGE
    return filteredTasks.slice(start, start + TASKS_PER_PAGE)
  }, [filteredTasks, currentPage])

  useEffect(() => {
    if (filteredTasks.length === 0) {
      setSelectedTaskId(null)
      return
    }

    const exists = filteredTasks.some((task) => task.id === selectedTaskId)
    if (!exists) {
      setSelectedTaskId(filteredTasks[0].id)
    }
  }, [filteredTasks, selectedTaskId])

  const selectedTask = useMemo(
    () => filteredTasks.find((t) => t.id === selectedTaskId) || null,
    [filteredTasks, selectedTaskId],
  )

  const isLogOpenForSelectedTask =
    !!selectedTask && !!showLogByTask[selectedTask.id]

  const selectedTaskStatus = selectedTask
    ? getStatusConfig(selectedTask.status)
    : null

  const selectedTaskMainDate = selectedTask
    ? getMainDateByStatus(selectedTask)
    : null

  const canDownloadProcessingLog =
    !!selectedTask &&
    ["finished", "error"].includes(selectedTask.status)

  const selectedTaskOriginalVideoFile = useMemo(
    () =>
      (selectedTask?.outputs ?? []).find((filename) =>
        /\.original\.subtitled\.mp4$/i.test(String(filename)),
      ) || null,
    [selectedTask],
  )

  const selectedTaskAudioFile = useMemo(
    () =>
      (selectedTask?.outputs ?? []).find((filename) =>
        /\.mp3$/i.test(String(filename)),
      ) || null,
    [selectedTask],
  )

  const selectedTaskJsonFiles = useMemo(
    () => getJsonPreviewItems(selectedTask?.outputs ?? []),
    [selectedTask],
  )
  const selectedTaskVisibleJsonFiles = useMemo(
    () => selectedTaskJsonFiles.filter((item) => item.key !== "original"),
    [selectedTaskJsonFiles],
  )


  const selectedTaskCurrentJsonFile =
    selectedTaskJsonFiles.find((item) => item.key === selectedJsonTab) ||
    selectedTaskJsonFiles[0] ||
    null

  const selectedTaskCurrentDownloadMeta = useMemo(() => {
    const key = selectedTaskCurrentJsonFile?.key

    if (key && LANGUAGE_META[key]) {
      return LANGUAGE_META[key]
    }

    return { label: "Idioma", icon: null }
  }, [selectedTaskCurrentJsonFile])

  const selectedTaskCurrentJsonCacheKey =
    selectedTask && selectedTaskCurrentJsonFile
      ? getPreviewCacheKey(selectedTask.id, selectedTaskCurrentJsonFile.filename)
      : null

  const selectedTaskCurrentDownloadFiles = useMemo(() => {
    const outputs = selectedTask?.outputs ?? []
    const key = selectedTaskCurrentJsonFile?.key

    if (!key) {
      return {
        txt: null,
        srt: null,
        vtt: null,
        json: null,
        html: null,
        pdf: null,
        video: null,
      }
    }

    return {
      txt: findVariantOutput(outputs, key, "txt"),
      srt: findVariantOutput(outputs, key, "srt"),
      vtt: findVariantOutput(outputs, key, "vtt"),
      json: selectedTaskCurrentJsonFile.filename,
      html: findVariantOutput(outputs, key, "html"),
      pdf: findVariantOutput(outputs, key, "pdf"),
      video: findSubtitledVideoOutput(outputs, key),
    }
  }, [selectedTask, selectedTaskCurrentJsonFile])
 
  const selectedTaskIsDocument = selectedTask?.task_type === "documents"

  const selectedTaskDocumentOriginalFile = useMemo(() => {
    if (!selectedTaskIsDocument) return null

    return selectedTask?.input_filename || null
  }, [selectedTask, selectedTaskIsDocument])

  const selectedTaskCurrentDocumentPreview = getDocumentPreviewData(
    selectedTaskCurrentJsonCacheKey
      ? previewJsonByFile[selectedTaskCurrentJsonCacheKey]
      : null,
  )

  const selectedTaskDocumentCategorySummaries = useMemo(
    () => buildDocumentCategorySummaries(selectedTaskCurrentDocumentPreview),
    [selectedTaskCurrentDocumentPreview],
  )

  const selectedTaskDocumentGlobalScore = useMemo(
    () => buildGlobalDocumentScore(selectedTaskDocumentCategorySummaries),
    [selectedTaskDocumentCategorySummaries],
  )

  const selectedTaskDocumentGlobalTone = useMemo(
    () => getDocumentScoreTone(selectedTaskDocumentGlobalScore),
    [selectedTaskDocumentGlobalScore],
  )

  const selectedTaskDocumentGlobalSummary = useMemo(
    () => buildGlobalDocumentSummary(selectedTaskDocumentCategorySummaries),
    [selectedTaskDocumentCategorySummaries],
  )

  const selectedTaskCurrentVideoFile =
    selectedTaskCurrentDownloadFiles.video || selectedTaskOriginalVideoFile || null

  const selectedTaskCurrentSegments =
    selectedTaskCurrentJsonCacheKey &&
      previewJsonByFile[selectedTaskCurrentJsonCacheKey]?.segments
      ? previewJsonByFile[selectedTaskCurrentJsonCacheKey].segments
      : []

  useEffect(() => {
    setCurrentAudioTime(0)
  }, [selectedTask?.id, selectedTaskAudioFile, selectedTaskCurrentVideoFile])

  const activeSegmentId = useMemo(() => {
    const activeSegment = selectedTaskCurrentSegments.find(
      (segment) =>
        currentAudioTime >= Number(segment.start ?? 0) &&
        currentAudioTime < Number(segment.end ?? 0),
    )

    return activeSegment?.id ?? null
  }, [selectedTaskCurrentSegments, currentAudioTime])

  useEffect(() => {
    if (selectedTaskJsonFiles.length === 0) return

    setSelectedJsonTab((prev) =>
      selectedTaskJsonFiles.some((item) => item.key === prev)
        ? prev
        : selectedTaskJsonFiles[0].key,
    )
  }, [selectedTaskJsonFiles])

  useEffect(() => {
    if (!selectedTask || !selectedTaskCurrentJsonFile) return
    if (!selectedTaskCurrentJsonCacheKey) return
    if (previewJsonByFile[selectedTaskCurrentJsonCacheKey] !== undefined) return
    if (loadingJsonPreviewKey === selectedTaskCurrentJsonCacheKey) return

    loadJsonPreview(selectedTask.id, selectedTaskCurrentJsonFile.filename)
  }, [
    selectedTask,
    selectedTaskCurrentJsonFile,
    selectedTaskCurrentJsonCacheKey,
    previewJsonByFile,
    loadingJsonPreviewKey,
  ])
  useEffect(() => {
    if (activeSegmentId === null) return

    const element = segmentRefs.current[activeSegmentId]
    if (!element) return

    element.scrollIntoView({
      behavior: "smooth",
      block: "nearest",
    })
  }, [activeSegmentId])

  useEffect(() => {
    if (!selectedTask) return
    if (!isLogOpenForSelectedTask) return

    refreshLogSilently(selectedTask.id)

    if (!isTaskActive(selectedTask)) return

    const interval = setInterval(() => {
      refreshLogSilently(selectedTask.id)
    }, 2000)

    return () => clearInterval(interval)
  }, [
    selectedTask?.id,
    selectedTask?.status,
    isLogOpenForSelectedTask,
  ])

  useEffect(() => {
    if (!selectedTask) return
    if (!isLogOpenForSelectedTask) return
    if (!logScrollRef.current) return

    const el = logScrollRef.current
    el.scrollTop = el.scrollHeight
  }, [
    logsByTask[selectedTask?.id],
    selectedTask?.id,
    selectedTask?.status,
    isLogOpenForSelectedTask,
  ])

  return (
    <div className="min-h-screen">
      <header className="bg-color-primary backdrop-blur border-b border-slate-200 sticky top-0 z-50">
        <div className="relative mx-auto max-w-7xl px-4 py-3 flex items-center justify-between">
          <img
            src={AIUDA_NEGATIVE_LOGOS_SRC}
            alt="Aiuda"
            className="h-10 w-auto"
          />
          <nav className="flex items-center gap-6 text-normal font-medium text-slate-700">
            <a href="#" className="hover:text-slate-900 active">CREAR</a>
            <a href="#buscar" className="flex items-center gap-2 hover:opacity-80">
              BUSCAR
              <Search className="h-4 w-4" />
            </a>
          </nav>
          
          <button onClick={() => setMenuOpen(!menuOpen)} className="md:hidden text-white">
            {menuOpen ? <X /> : <Menu />}
          </button>
          <nav className="hidden md:flex items-center gap-6 text-normal font-medium text-slate-700">
            {languagesNav.map((lng) => (
              <button
                key={lng}
                onClick={() => changeLanguage(lng)}
                className={lang === lng ? "active" : ""}
              >
                {lng.toUpperCase()}
              </button>
            ))}

            <button onClick={toggleProfile} className="flex items-center">
              <UserCog className="h-5 w-5 mr-2" />
              {profile === "teacher" ? "Docente" : "Técnico"}
            </button>
          </nav>
          <nav
            className={`
              absolute top-full right-0 w-full bg-white shadow-lg p-4
              flex-col gap-4 text-normal font-medium text-slate-700 bg-color-primary
              ${menuOpen ? "flex" : "hidden"}
              md:hidden
            `}
          >
            {languagesNav.map((lng) => (
              <button
                key={lng}
                onClick={() => {
                  changeLanguage(lng)
                  setMenuOpen(false)
                }}
                className={lang === lng ? "active" : ""}
              >
                {lng.toUpperCase()}
              </button>
            ))}

            <button
              onClick={() => {
                toggleProfile()
                setMenuOpen(false)
              }}
              className="flex items-center"
            >
              <UserCog className="h-5 w-5 mr-2" />
              {profile === "teacher" ? "Docente" : "Técnico"}
            </button>
          </nav>
        </div>
      </header>
      <section className="mx-auto max-w-7xl px-4 py-8 md:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row gap-10 mb-8">
          <article className="md:w-1/2">
            <div className="border-primary p-6 rounded-[2rem]">
              <div className="max-w-3xl text-center">
                <div className="mb-4 text-center">
                  <img
                    src={AIUDA_LOGOS_SRC}
                    alt="Aiuda"
                    className="logo"
                  />
                </div>
                <p className="text-base leading-7 text-slate-600 text-center mb-2">
                  {t("title")}
                </p>
                <div className="bg-color-primary p-4 text-white text-center new-rounded">
                  <a></a>
                  <h3>
                    <strong>Aiuda </strong> {t("slogan")}
                  </h3>
                </div>
                <h4 className="mt-4 text-xl font-semibold color-primary">{t("intro-question")}</h4>
              </div>
              <div className="features">
                  <div className="feature-title w-auto new-rounded py-2 mt-4 mb-2 font-semibold color-primary inline-block">
                      <h4 className="flex align-items-center text-lg font-semibold">
                        VIDEO / AUDIO
                      </h4>
                  </div>
                  <div className="flex gap-6">
                    <div className="w-1/3 text center">
                        <Captions className="m-auto w-10 h-10"></Captions>
                        <h4 className="text-center text-base">Subtítulos del video</h4>
                    </div>
                    <div className="w-1/3 text center">
                        <ListMinus className="m-auto w-10 h-10"></ListMinus>
                        <h4 className="text-center text-base">Versión en texto</h4>
                    </div>
                    <div className="w-1/3 text center">
                        <Languages className="m-auto w-10 h-10"></Languages>
                        <h4 className="text-center text-base">Traducción a otros idiomas</h4>
                    </div>
                  </div>
              </div>
              <div className="features ">
                  <div className="feature-title w-auto new-rounded py-2 mt-4 mb-2 font-semibold color-primary inline-block">
                      <h4 className="flex align-items-center text-lg font-semibold">
                         DOCUMENTOS
                      </h4>
                      
                  </div>
                  <div className="flex gap-6">
                    <div className="w-1/3 text center">
                        <PersonStanding className="m-auto w-10 h-10"></PersonStanding>
                        <h4 className="text-center text-base">Evaluación de Accesibilidad</h4>
                    </div>
                    <div className="w-1/3 text center">
                        <PaintBucket className="m-auto w-10 h-10"></PaintBucket>
                        <h4 className="text-center text-base">Baja Visión / Color</h4>
                    </div>
                    <div className="w-1/3 text center">
                        <CaseSensitive className="m-auto w-10 h-10"></CaseSensitive>
                        <h4 className="text-center text-base">Tamaño de letra</h4>
                    </div>
                  </div>
              </div>
              <div className="flex flex-col lg:flex-row gap-2 md:gap-10 mt-6">
                <div className="lg:w-1/2">
                  {acceptedTerms && (
                    <>
                      <h4 className="font-semibold flex mb-2"><Mail className="mr-2"></Mail> Aviso por correo:</h4>
                      <p className="text-sm">Aiuda te enviará una notificación cuando el procesamiento haya finalizado, con el código necesario para localizar tu tarea.</p>
                    </>
                  )}
                </div>
                <div className="lg:w-1/2">
                  <h4 className="font-semibold mb-2">Idiomas disponibles:</h4>
                  <div className="flex gap-2">
                    <div className="text-center">
                        <div className="lang">
                          ES
                        </div>
                        <p className="text-sm">Español</p>
                    </div>
                    <div className="text-center">
                        <div className="lang">
                          GL
                        </div>
                        <p className="text-sm">Gallego</p>
                    </div>
                    <div className="text-center">
                        <div className="lang">
                          PT
                        </div>
                        <p className="text-sm">Portugués</p>
                    </div>
                    <div className="text-center">
                        <div className="lang">
                          EN
                        </div>
                        <p className="text-sm">Inglés</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </article>

          <article className="mb-6 md:w-1/2">
            <Card className="rounded-[2rem] border-primary">
              <CardHeader className="">
                <div className="flex items-start gap-3">
                  <div>
                    <CardTitle className="text-lg text-slate-950 items-center flex text-white new-rounded text-color-primary font-bold px-2">
                      NUEVA TAREA
                    </CardTitle>
                  </div>
                </div>
              </CardHeader>

              <CardContent>
                <form onSubmit={submitTask} className="space-y-6">
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-3">
                      <button
                        type="button"
                        onClick={() => handleModeChange("multimedia")}
                        className={`rounded-2xl border px-4 py-2 text-left transition ${form.mode === "multimedia"
                            ? "border-primary2-200 bg-primary2-70 shadow-sm text-white"
                            : "border-slate-200 bg-white"
                          }`}
                      >
                        <div className="flex items-center gap-2">
                          <CirclePlay className="h-6 w-6" />
                          <span className="text-lg font-semibold">
                            MULTIMEDIA
                          </span>
                        </div>
                      </button>

                      <button
                        type="button"
                        onClick={() => handleModeChange("documental")}
                        className={`rounded-2xl border px-4 py-2 text-left transition ${form.mode === "documental"
                            ? "border-primary2-200 bg-primary2-70 shadow-sm text-white"
                            : "border-slate-200 bg-white"
                          }`}
                      >
                        <div className="flex items-center gap-1">
                          <Presentation className="h-5 w-5" />
                          <FileText className="h-5 w-5" />
                          <span className="text-lg font-semibold">
                            DOCUMENTOS
                          </span>
                        </div>
                      </button>
                    </div>
                  </div>
                  {form.mode === "multimedia" ? (
                    <div className="space-y-2">
                      <div className="flex gap-3">
                        <button
                          type="button"
                          onClick={() => handleMediaTypeChange("video")}
                          className={`flex items-center gap-2 rounded-xl border px-4 py-3 transition font-semibold ${
                            form.mediaType === "video"
                              ? "border-primary bg-sky-50"
                              : "border-slate-300 bg-white hover:bg-slate-50"
                          }`}
                        >
                          <Video></Video>
                          VIDEO
                        </button>
                        <button
                          type="button"
                          onClick={() => handleMediaTypeChange("audio")}
                          className={`flex items-center gap-2 rounded-xl border px-4 py-3 transition ${
                            form.mediaType === "audio"
                              ? "border-primary bg-sky-50"
                              : "border-slate-300 bg-white hover:bg-slate-50"
                          }`}
                        >
                          <Volume2></Volume2>
                          Audio
                        </button>

                      </div>
                    </div>
                  ) : null}
                  

                  {/*--INPUT FILE--*/}
                  <div className="space-y-2">
                    <Label htmlFor="aluda-file-input" className="hidden">Archivo:</Label>

                    <input
                      id="aluda-file-input"
                      type="file"
                      accept={getAcceptForForm(form.mode, form.mediaType)}
                      onChange={(e) => { setSelectedFile(e.target.files?.[0] ?? null); setErrors({}) }}
                      className="hidden"
                    />

                    <label
                      htmlFor="aluda-file-input"
                      onDragOver={(e) => {
                        e.preventDefault()
                        setIsDraggingFile(true)
                      }}
                      onDragLeave={() => setIsDraggingFile(false)}
                      onDrop={(e) => {
                        e.preventDefault()
                        setIsDraggingFile(false)
                        const file = e.dataTransfer.files?.[0] ?? null
                        setSelectedFile(file)
                        setErrors({})
                      }}
                      className={`border-file-input flex flex-col items-center cursor-pointer rounded-2xl border px-4 py-3 transition ${isDraggingFile
                          ? "border-sky-400 bg-sky-50"
                          : "border-slate-300 bg-white hover:bg-slate-50"
                        }`}
                    >
                      <div className="min-w-0">
                        <div className="circle-type">
                            {form.mode === "multimedia"
                          ? form.mediaType === "video"
                            ? <Video className="w-10 h10"></Video>
                            : <Volume2></Volume2>
                          : <Presentation></Presentation>}
                        </div>
                        <p className="text-xl font-semibold text-center">
                          {selectedFile ? selectedFile.name : "Seleccionar archivo"}
                        </p>
                        <p className="text-base font-normal">
                          {selectedFile
                            ? "Pulsa o arrastra otro archivo para cambiarlo"
                            : "Haz clic o arrastra aquí tu archivo"}
                        </p>
                      </div>
                      <p className="text-xs text-slate-500">
                        {form.mode === "multimedia"
                          ? form.mediaType === "video"
                            ? "Formatos habituales: MP4, MOV, AVI, WMV, MKV y WebM"
                            : "Formatos habituales: MP3, WAV, M4A y OGG."
                          : "Formatos habituales:.pdf,.ppt,.pptx,.doc,.docx"}
                      </p>

                      <div className="mt-2 ml-4 shrink-0 rounded-xl bg-color-primary px-3 py-2 text-sm font-medium text-white">
                        Examinar
                      </div>
                    </label>
                    {errors.file && (
                      <p className="text-sm text-red-600">{errors.file}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email" className="text-semibold text-base">Correo Electrónico:</Label>
                    <Input
                      id="email"
                      type="email"
                      className={`h-12 rounded-xl bg-white ${
                        errors.email ? "border-red-300" : "border-slate-300"
                      }`}
                      value={form.email}
                      onChange={(e) =>
                        setForm((prev) => ({ ...prev, email: e.target.value }))
                      }
                      placeholder="Ingresar dirección de correo, por ejemplo nombre@universidad.com"
                    />
                    {errors.email && (
                      <p className="text-sm text-red-600">{errors.email}</p>
                    )}
                    <p className="text-xs text-slate-500">
                      Usaremos este correo para enviarte una notificación, cuando el procesamiento haya finalizado, con el código necesario para localizar tu tarea.
                    </p>
                    
                  </div>
                  {/*BLOQUE FER*/}
                  <div className="hidden">
                    <div className="rounded-2xl bg-slate-50">
                        {form.mode === "multimedia" ? (
                          <>
                            {form.mediaType === "video" && (
                              <div className="rounded-xl bg-white px-3">
                                {form.options.burn_subtitles && (
                                  <div className="pt-1">
                                    <p className="text-xs text-slate-500 mb-2">Idiomas para video subtitulado:</p>
                                    <div className="flex flex-wrap gap-2">
                                      {[{ code: "original", label: "Original", icon: "🎬" }, ...TARGET_LANGS].map((lang) => {
                                        const active = (form.options.burn_langs || []).includes(lang.code)
                                        return (
                                          <button
                                            key={lang.code}
                                            type="button"
                                            onClick={() => {
                                              const current = new Set(form.options.burn_langs || [])
                                              if (active) current.delete(lang.code)
                                              else current.add(lang.code)
                                              setOption("burn_langs", Array.from(current))
                                            }}
                                            className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium border transition-colors ${
                                              active
                                                ? "bg-sky-100 border-sky-300 text-sky-800"
                                                : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
                                            }`}
                                          >
                                            {lang.label}
                                          </button>
                                        )
                                      })}
                                    </div>
                                  </div>
                                )}
                              </div>
                            )}

                            {form.mediaType === "video" && (
                              <div className="rounded-xl bg-white">
                                <Label className="text-base">Formatos de salida</Label>
                                <p className="text-xs text-slate-500 mb-2">
                                  Seleccioná qué archivos generar para cada idioma.
                                </p>
                                <div className="flex flex-wrap gap-2">
                                  {[
                                    { id: "srt", label: "SRT (subtítulos)" },
                                    { id: "vtt", label: "VTT (subtítulos web)" },
                                    { id: "txt", label: "TXT (texto plano)" },
                                    { id: "json", label: "JSON (datos)" },
                                  ].map(({ id, label }) => {
                                    const active = (form.options.output_formats || []).includes(id)
                                    return (
                                      <button
                                        key={id}
                                        type="button"
                                        onClick={() => {
                                          const current = new Set(form.options.output_formats || [])
                                          if (active) current.delete(id)
                                          else current.add(id)
                                          setOption("output_formats", Array.from(current))
                                        }}
                                        className={`rounded-full px-3 py-1 text-base font-medium border transition-colors ${
                                          active
                                            ? "bg-sky-100 border-sky-300 text-sky-800"
                                            : "bg-white border-slate-200 text-slate-500"
                                        }`}
                                      >
                                        {label}
                                      </button>
                                    )
                                  })}
                                </div>
                              </div>
                            )}
                          </>
                        ) : (
                          <>
                            <div className="rounded-xl bg-white px-3 py-3 space-y-2">
                              {form.options.translation && (
                                <div className="pt-1">
                                  <p className="text-base mb-2 font-medium">Idiomas destino:</p>
                                  <div className="flex flex-wrap gap-2">
                                    {TARGET_LANGS.map((lang) => {
                                      const active = (form.options.file_langs || []).includes(lang.code)
                                      return (
                                        <button
                                          key={lang.code}
                                          type="button"
                                          onClick={() => {
                                            const current = new Set(form.options.file_langs || [])
                                            if (active) current.delete(lang.code)
                                            else current.add(lang.code)
                                            setOption("file_langs", Array.from(current))
                                          }}
                                          className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-base font-medium border transition-colors ${
                                            active
                                              ? "bg-sky-100 border-sky-300 text-sky-800"
                                              : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
                                          }`}
                                        >
                                          {lang.label}
                                        </button>
                                      )
                                    })}
                                  </div>
                                </div>
                              )}
                            </div>
                          </>
                        )}

                    </div>
                    <Separator />
                    {form.mode === "multimedia" && (
                      <div className="space-y-4">
                        <div className="space-y-3">
                          <Label className="text-base mb-0 mt-2">Idiomas para archivos</Label>
                          <p className="text-xs text-slate-500">
                            Seleccioná en qué idiomas generar los archivos de subtítulos y texto.
                          </p>
                          <div className="flex flex-wrap gap-2">
                            {TARGET_LANGS.map((lang) => {
                              const active = (form.options.file_langs || []).includes(lang.code)
                              const enabled = (form.options.output_formats || []).length > 0
                              return (
                                <button
                                  key={lang.code}
                                  type="button"
                                  disabled={!enabled}
                                  onClick={() => {
                                    const current = new Set(form.options.file_langs || [])
                                    if (active) current.delete(lang.code)
                                    else current.add(lang.code)
                                    setOption("file_langs", Array.from(current))
                                  }}
                                  className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-base font-medium border transition-colors ${
                                    !enabled
                                      ? "opacity-40 cursor-not-allowed bg-white border-slate-200 text-slate-400"
                                      : active
                                      ? "bg-sky-100 border-sky-300 text-sky-800"
                                      : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
                                  }`}
                                >
                                  {lang.label}
                                </button>
                              )
                            })}
                          </div>
                        </div>
                      </div>
                      )}
                  </div>
                  {/*FIN BLOQUE FER*/}
                  <div className="flex items-start gap-2">
                    <input
                      type="checkbox"
                      id="terms"
                      checked={acceptedTerms}
                      onChange={(e) => setAcceptedTerms(e.target.checked)}
                      className="mt-1"
                    />

                    <label htmlFor="terms" className="text-sm text-slate-700">
                      Acepto los{" "}
                      <button
                        type="button"
                        onClick={() => setShowTerms(true)}
                        className="text-blue-600 underline"
                      >
                        términos y condiciones
                      </button>
                    </label>
                  </div>
                  <Button
                    className="h-12 w-full btn-color-primary-2 rounded-xl bg-slate-900 text-white hover:bg-slate-800"
                    type="submit"
                    disabled={!acceptedTerms || submitting}
                  >
                    Enviar Archivo
                    {submitting ? (
                      <Loader2 className="ml-2 h-5 w-5 animate-spin" />
                    ) : (
                      <Upload className="ml-2 h-6 w-6" />
                    )}
                  </Button>

                  <Separator />

                </form>
                {showTerms && <Terms onClose={() => setShowTerms(false)} />}
                {uiError ? (
                  <div className="mb-6 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 shadow-sm">
                    {uiError}
                  </div>
                ) : null}
                {success && (
                  <div className="rounded-2xl border-success bg-success-50 px-4 py-3 text-sm text-green-700">
                    <p className="text-lg text-center">
                      ¡Recibimos tu archivo!
                    </p>
                    <p>
                         Cuando el proceso haya finalizado recibirás una notificación por correo electrónico con el código necesario para localizar la tarea.
                    </p>
                    
                  </div>
                )}
                
              </CardContent>
            </Card>
          </article>
          
        </div>
        <article>
          <div className="flex flex-col md:flex-row md:space-y-0 space-y-4 justify-between items-center" id="buscar">
                <div className="flex items-start gap-3">
                  <div>
                    <CardTitle className="text-lg text-color-primary py-1 px-4 font-bold text-lg">
                        LOCALIZÁ TU TAREA
                    </CardTitle>
                  </div>
                </div>
                {profile === "technical" && (
                  <div className="flex gap-2 justify-end">
                    {[
                      { key: "all", label: "Todas" },
                      { key: "active", label: "Activas" },
                      { key: "finished", label: "Finalizadas" },
                      { key: "error", label: "Errores" },
                    ].map((item) => (
                      <button
                        key={item.key}
                        type="button"
                        onClick={() => setFilter(item.key)}
                        className={`rounded-full border px-3 py-2 text-sm text-center transition ${filter === item.key
                            ? "bg-color-primary text-white"
                            : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
                          }`}
                      >
                        {item.label}
                      </button>
                    ))}
                  </div>
                )}
          </div>
          <div className="mb-6 space-y-2 mt-2">
            <Input
              id="task-search-id"
              className="h-11 rounded-xl border-slate-300 bg-white"
              value={searchId}
              onChange={(e) => setSearchId(e.target.value)}
              placeholder="Ingresá el código que recibiste por correo electrónico"
            />
            <p className="text-xs mb-2">
              En este campo podrás recuperar una tarea concreta, consultar su estado o descargar tus resultados.
            </p>
          </div>
        </article>
        {profile === "technical" && (
          <article>
            <div className="mb-8 grid gap-4 grid-cols-2 md:grid-cols-4 xl:grid-cols-6">
              <MetricCard title="En cola" value={counts.queued} icon={Clock3} tone="amber" />
              <MetricCard
                title="Procesando"
                value={counts.processing}
                icon={Loader2}
                tone="blue"
              />
              <MetricCard
                title="Finalizadas"
                value={counts.finished}
                icon={CheckCircle2}
                tone="green"
              />
              <MetricCard
                title="Con error"
                value={counts.error}
                icon={AlertTriangle}
                tone="rose"
              />
              <MetricCard
                title="Notificadas"
                value={counts.notified}
                icon={Mail}
                tone="slate"
              />
            </div>
          </article>
        )}
        <div className="flex flex-col md:flex-row gap-6">
          <Card className="md:w-1/2 rounded-[2rem] border-primary">
            <CardContent>
              {filteredTasks.length === 0 ? (
                <div className="rounded-[1.5rem] border border-dashed border-slate-300 bg-slate-50 px-6 py-16 text-center">
                  <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-white shadow-sm">
                    <Filter className="h-6 w-6 text-slate-500" />
                  </div>
                  <p className="text-sm font-medium text-slate-700">
                    {searchId.trim()
                      ? "No se encontró ningún trabajo con ese ID."
                      : "No hay tareas para este filtro."}
                  </p>
                  <p className="mt-1 text-sm text-slate-500">
                    {searchId.trim()
                      ? "Revisa el ID o cambia el filtro seleccionado."
                      : "Cuando envíes trabajos aparecerán aquí con su progreso."}
                  </p>
                </div>
              ) : (
                <>
                  <div className="space-y-3">
                    {paginatedTasks.map((task) => {
                      const status = getStatusConfig(task.status)
                      const Icon = getTaskIcon(task.task_type)
                      const StatusIcon = status.icon
                      const isSelected = task.id === selectedTaskId

                      return (
                        <button
                          key={task.id}
                          type="button"
                          onClick={() => handleTaskCardClick(task)}
                          className={`w-full rounded-2xl border px-4 py-4 text-left transition ${isSelected
                              ? "border-sky-300 bg-sky-50 shadow-sm"
                              : "border-slate-200 bg-white hover:bg-slate-50"
                            }`}
                        >
                          <div className="flex items-center gap-2">
                            <Badge className={`rounded-full px-2.5 py-0.5 ${status.badge}`}>
                              <StatusIcon
                                className={`mr-1.5 h-3.5 w-3.5 ${task.status === "processing" ? "animate-spin" : ""
                                  }`}
                              />
                              {status.label}
                            </Badge>

                            <Badge
                              variant="outline"
                              className="rounded-full px-2.5 py-0.5"
                            >
                              {getTaskTypeLabel(task.task_type)}
                            </Badge>
                          </div>

                          <div className="mt-3 flex items-start gap-3">
                            <div className="shrink-0 rounded-xl bg-slate-100 p-2.5 text-slate-700">
                              <Icon className="h-4 w-4" />
                            </div>

                            <div className="min-w-0 flex-1">
                              <p className="break-all text-sm font-medium text-slate-900">
                                {task.email || "-"}
                              </p>
                              <p className="mt-1 break-all text-xs text-slate-500">
                                ID: {task.id}
                              </p>
                            </div>
                          </div>

                          <div className="mt-4">
                            <div className="mb-2 flex items-center justify-between text-xs text-slate-500">
                              <span>Progreso</span>
                              <span>{task.progress ?? 0}%</span>
                            </div>

                            <div className="h-2 overflow-hidden rounded-full bg-slate-200">
                              <div
                                className={`h-full rounded-full transition-all ${status.bar}`}
                                style={{
                                  width: `${Math.max(
                                    0,
                                    Math.min(100, task.progress ?? 0),
                                  )}%`,
                                }}
                              />
                            </div>
                          </div>

                          <div className="mt-4 flex flex-col gap-2 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between">
                            <div className="flex min-w-0 items-center gap-2">
                              <Mail className="h-4 w-4 shrink-0" />
                              <span className="truncate">
                                Notificación:{" "}
                                <span className="font-medium text-slate-700">
                                  {getNotificationState(task)}
                                </span>
                              </span>
                            </div>

                            <div className="inline-flex shrink-0 items-center gap-1 text-slate-500">
                              <span>Ver detalle</span>
                              <ChevronRight className="h-4 w-4" />
                            </div>
                          </div>
                        </button>
                      )
                    })}
                  </div>

                  {filteredTasks.length > TASKS_PER_PAGE ? (
                    <div className="mt-5 flex items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                      <Button
                        type="button"
                        variant="outline"
                        className="h-10 rounded-xl"
                        onClick={() =>
                          setCurrentPage((prev) => Math.max(1, prev - 1))
                        }
                        disabled={currentPage === 1}
                      >
                        Anterior
                      </Button>
                      <span className="font-medium text-slate-800">
                        Página {currentPage} de {totalPages}
                      </span>
                      <Button
                        type="button"
                        variant="outline"
                        className="h-10 rounded-xl"
                        onClick={() =>
                          setCurrentPage((prev) => Math.min(totalPages, prev + 1))
                        }
                        disabled={currentPage === totalPages}
                      >
                        Siguiente
                      </Button>
                    </div>
                  ) : null}
                </>
              )}
            </CardContent>
          </Card>
          <Card className={`md:w-1/2 rounded-[2rem] border-primary`}>
            <CardHeader className="pb-4">
              <div className="flex items-end justify-between gap-3">
                <div>
                  <CardTitle className="text-lg text-color-primary font-bold py-1 px-2">
                      RESULTADOS
                  </CardTitle>
                </div>
                <div>
                  {selectedTask && (
                    <div className="mb-3 flex items-center gap-2">
                      <Badge
                        className={`rounded-full px-3 py-1 ${selectedTaskStatus.badge}`}
                      >
                        {selectedTaskStatus.label}
                      </Badge>
                      <Badge variant="outline" className="rounded-full px-3 py-1">
                        {getTaskTypeLabel(selectedTask.task_type)}
                      </Badge>
                    </div>
                  )}
                </div>
              </div>
            </CardHeader>

            <CardContent>
              {!selectedTask ? (
                <div className="rounded-[1.5rem] border border-dashed border-slate-300 bg-slate-50 px-6 py-16 text-center">
                  <p className="text-sm font-medium text-slate-700">
                    Selecciona una tarea para ver el detalle.
                  </p>
                </div>
              ) : (
                <div className="space-y-5">
                  <div className="rounded-[1.5rem] border border-slate-200 bg-white p-4 shadow-sm">
                    

                    <h3 className="text-lg font-semibold">
                      {selectedTask.resource || "Código"} : {selectedTask.id}
                    </h3>

                    <div className="mt-2 grid gap-2 text-normal">
                      {selectedTaskMainDate?.value ? (
                        <div className="rounded-xl bg-slate-50">
                          <span className="font-medium">
                            {selectedTaskMainDate.label}:
                          </span>{" "}
                          {formatDate(selectedTaskMainDate.value)}
                        </div>
                      ) : null}
                      <div className="rounded-xl bg-slate-50">
                        <span className="font-medium">Correo Electrónico:</span>{" "}
                        {selectedTask.email || "-"}
                      </div>
                      <div className="rounded-xl bg-slate-50 hidden">
                        <span className="font-medium">Notificación:</span>{" "}
                        {getNotificationState(selectedTask)}
                      </div>
                    </div>
                  </div>

                  <div>
                    <PipelineMini task={selectedTask} />
                  </div>
                  {selectedTask.notes ? (
                    <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                      <div className="mb-2 flex items-center gap-2">
                        <FileText className="h-4 w-4" />
                        <p className="text-base font-semibold">
                          Observaciones:
                        </p>
                      </div>

                      <p className="text-sm leading-6 text-slate-800 whitespace-pre-wrap">
                        {selectedTask.notes}
                      </p>
                    </div>
                  ) : null}

                  {selectedTask.error ? (
                    <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                      <span className="font-medium">Error:</span> {selectedTask.error}
                    </div>
                  ) : null}

                  {selectedTask?.task_type === "video" && selectedTaskCurrentVideoFile ? (
                    <div className="space-y-3">
                      <p className="text-sm font-medium text-slate-900">
                        Ver video subtitulado
                      </p>
                      <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                        <video
                          controls
                          className="w-full rounded-xl bg-black"
                          src={`/api/tasks/${selectedTask.id}/download/${encodeURIComponent(
                            selectedTaskCurrentVideoFile,
                          )}`}
                          onTimeUpdate={(e) => setCurrentAudioTime(e.currentTarget.currentTime)}
                        >
                          Tu navegador no soporta reproducción de video.
                        </video>

                        <div className="mt-3 flex items-center justify-between gap-3">
                          <p className="text-xs text-slate-500">
                            {selectedTaskCurrentJsonFile
                              ? `Subtítulos mostrados en ${selectedTaskCurrentDownloadMeta.label}.`
                              : "video con subtítulos incrustados."}
                          </p>

                          <Button
                            type="button"
                            variant="download"
                            className="h-9 rounded-xl"
                            size="md"
                            onClick={() => downloadGroup(selectedTask.id, [selectedTaskCurrentVideoFile])}
                          >
                            <Download className="mr-2 h-4 w-4" />
                            Descargar video
                          </Button>
                        </div>
                      </div>
                    </div>
                  ) : null}

                  {selectedTaskAudioFile ? (
                    <div className="space-y-3">
                      <p className="text-base font-medium">
                        Reproducir Audio
                      </p>
                      <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                        <audio
                          ref={audioPlayerRef}
                          controls
                          className="w-full"
                          src={`/api/tasks/${selectedTask.id}/download/${encodeURIComponent(
                            selectedTaskAudioFile,
                          )}`}
                          onTimeUpdate={(e) => setCurrentAudioTime(e.currentTarget.currentTime)}
                        >
                          Tu navegador no soporta reproducción de audio.
                        </audio>

                        <div className="mt-3 flex items-center justify-between gap-3">
                          <p className="text-xs text-slate-500"></p>

                          <Button
                            type="button"
                            variant="download"
                            className="h-9 rounded-xl hidden"
                            size="md"
                            onClick={() => downloadGroup(selectedTask.id, [selectedTaskAudioFile])}
                          >
                            <Download className="mr-2 h-4 w-4" />
                            Descargar Audio
                          </Button>
                        </div>
                      </div>
                    </div>
                  ) : null}
                  {selectedTask?.task_type === "documents" ?(
                    <div className="space-y-3 mt-10">
                      <h3 className="text-base mb-2">Analizamos tu presentación en busca de oportunidades de mejora para ayudarte a crear materiales más claros y accesibles. <br />El análisis considera:</h3>
                      <ul className="mb-10 mt-4">
                        <li className="mb-4">
                          <h4 className="text-base font-semibold">Comprensión visual</h4>
                          <p className="text-base">
                            Tamaño de letra, interlineado, tipografía, cantidad de texto, color y contraste.
                          </p>
                        </li>
                        <li className="mb-4">
                          <h4 className="text-base font-semibold">Organización del contenido</h4>
                          <p className="text-base">
                            Jerarquía visual y cantidad de elementos por diapositiva.
                          </p>
                        </li>
                        <li className="mb-4">
                          <h4 className="text-base font-semibold">Uso de imágenes</h4>
                          <p className="text-base">
                            Presencia de descripciones.
                          </p>
                        </li>
                        <li className="mb-4">
                          <h4 className="text-base font-semibold">Tiempo de lectura</h4>
                          <p className="text-base">
                            Estimación del tiempo total de la presentación
                          </p>
                        </li>
                      </ul>                         
                    </div>
                  ) : null}
                  {selectedTaskJsonFiles.length > 0 ? (
                    <div className="space-y-3">
                      <h4 className="text-lg font-medium">
                        {selectedTaskIsDocument ? "Informe de Accesibilidad del Documento" : "Ver transcripción"}
                      </h4>

                      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                        {selectedTaskVisibleJsonFiles.length > 0 ? (
                          <div className="mb-3 flex flex-wrap gap-2">
                            {selectedTaskVisibleJsonFiles.map((item) => (
                              <button
                                key={item.key}
                                type="button"
                                onClick={() => setSelectedJsonTab(item.key)}
                                className={`rounded-full border px-3 py-1.5 text-sm transition ${
                                  selectedJsonTab === item.key
                                    ? "border-slate-900 bg-slate-900 text-white"
                                    : "border-slate-200 bg-white text-slate-700"
                                }`}
                              >
                                {item.label}
                              </button>
                            ))}
                          </div>
                        ) : null}

                        <div className="rounded-xl border border-slate-200 bg-white p-4">
                          {selectedTaskCurrentJsonCacheKey &&
                          loadingJsonPreviewKey === selectedTaskCurrentJsonCacheKey ? (
                            <div className="flex items-center gap-2 text-sm text-slate-500">
                              <Loader2 className="h-4 w-4 animate-spin" />
                              Cargando vista previa...
                            </div>
                          ) : selectedTaskCurrentJsonCacheKey &&
                            previewJsonByFile[selectedTaskCurrentJsonCacheKey]?.error ? (
                            <div className="text-sm text-red-600">
                              {previewJsonByFile[selectedTaskCurrentJsonCacheKey].error}
                            </div>
                          ) : selectedTaskIsDocument ? null : selectedTaskCurrentJsonCacheKey &&
                            previewJsonByFile[selectedTaskCurrentJsonCacheKey]?.segments?.length > 0 ? (
                            <div className="max-h-80 space-y-3 overflow-auto">
                              {previewJsonByFile[selectedTaskCurrentJsonCacheKey].segments.map(
                                (segment) => {
                                  const isActive =
                                    currentAudioTime >= Number(segment.start ?? 0) &&
                                    currentAudioTime < Number(segment.end ?? 0)

                                  return (
                                    <div
                                      key={segment.id}
                                      ref={(el) => {
                                        if (el) segmentRefs.current[segment.id] = el
                                      }}
                                      className={`rounded-xl border px-3 py-3 transition ${
                                        isActive
                                          ? "border-sky-300 bg-sky-50 shadow-sm"
                                          : "border-slate-200 bg-slate-50"
                                      }`}
                                    >
                                      <div
                                        className={`mb-1 text-xs font-medium ${
                                          isActive ? "text-sky-800" : "text-sky-700"
                                        }`}
                                      >
                                        {formatSeconds(segment.start)} - {formatSeconds(segment.end)}
                                      </div>
                                      <p
                                        className={`text-sm leading-6 ${
                                          isActive ? "text-slate-900" : "text-slate-700"
                                        }`}
                                      >
                                        {segment.text}
                                      </p>
                                    </div>
                                  )
                                },
                              )}
                            </div>
                          ) : (
                            <div className="text-sm text-slate-500">
                              No hay segmentos disponibles para esta vista.
                            </div>
                          )}
                        </div>

                        <div className="mt-3 flex flex-col gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3">
                          <div className="flex items-center gap-2 text-sm font-medium text-slate-700">
                            {selectedTaskCurrentDownloadMeta.icon === "/galicia-icon.png" ? (
                              <img
                                src={selectedTaskCurrentDownloadMeta.icon}
                                alt={selectedTaskCurrentDownloadMeta.label}
                                className="h-6 w-6 rounded-sm object-contain"
                              />
                            ) : selectedTaskCurrentDownloadMeta.icon ? (
                              <span className="leading-none hidden">{selectedTaskCurrentDownloadMeta.icon}</span>
                            ) : null}

                            <span>
                              {selectedTaskIsDocument
                                ? selectedTaskCurrentJsonFile?.key === "original"
                                  ? "Descargas disponibles"
                                  : `Descargas en ${selectedTaskCurrentDownloadMeta.label}`
                                : selectedTaskCurrentJsonFile?.key === "original"
                                ? "Descargas disponibles"
                                : `Descargas en ${selectedTaskCurrentDownloadMeta.label}`}
                            </span>
                          </div>

                          {selectedTaskIsDocument ? (
                            <div className="grid grid-cols-1 xl:grid-cols-2 gap-2 items-stretch">
                              {selectedTaskDocumentOriginalFile ? (
                                <Button
                                  type="button"
                                  variant="outline"
                                  className="h-9 w-full justify-center rounded-xl"
                                  onClick={() =>
                                    downloadGroup(selectedTask.id, [selectedTaskDocumentOriginalFile])
                                  }
                                >
                                  <Download className="mr-2 h-4 w-4" />
                                  Original
                                </Button>
                              ) : null}

                              {selectedTaskCurrentDownloadFiles.pdf ? (
                                <Button
                                  type="button"
                                  variant="outline"
                                  className="h-9 w-full justify-center rounded-xl"
                                  onClick={() =>
                                    downloadGroup(selectedTask.id, [selectedTaskCurrentDownloadFiles.pdf])
                                  }
                                >
                                  <Download className="mr-2 h-4 w-4" />
                                   Descargar recomendaciones
                                </Button>
                              ) : null}
                            </div>
                          ) : (
                            <div className="grid grid-cols-2 gap-2">
                              {selectedTaskCurrentDownloadFiles.txt ? (
                                <Button
                                  type="button"
                                  variant="outline"
                                  className="h-9 w-full justify-center rounded-xl"
                                  onClick={() =>
                                    downloadGroup(selectedTask.id, [selectedTaskCurrentDownloadFiles.txt])
                                  }
                                >
                                  <Download className="mr-2 h-4 w-4" />
                                  Texto
                                </Button>
                              ) : null}

                              {selectedTaskCurrentDownloadFiles.srt ? (
                                <Button
                                  type="button"
                                  variant="outline"
                                  className="h-9 w-full justify-center rounded-xl"
                                  onClick={() =>
                                    downloadGroup(selectedTask.id, [selectedTaskCurrentDownloadFiles.srt])
                                  }
                                >
                                  <Download className="mr-2 h-4 w-4" />
                                  SRT
                                </Button>
                              ) : null}

                              {selectedTaskCurrentDownloadFiles.vtt ? (
                                <Button
                                  type="button"
                                  variant="outline"
                                  className="h-9 w-full justify-center rounded-xl"
                                  onClick={() =>
                                    downloadGroup(selectedTask.id, [selectedTaskCurrentDownloadFiles.vtt])
                                  }
                                >
                                  <Download className="mr-2 h-4 w-4" />
                                  VTT
                                </Button>
                              ) : null}

                              {selectedTaskCurrentDownloadFiles.json ? (
                                <Button
                                  type="button"
                                  variant="outline"
                                  className="h-9 w-full justify-center rounded-xl"
                                  onClick={() =>
                                    downloadGroup(selectedTask.id, [selectedTaskCurrentDownloadFiles.json])
                                  }
                                >
                                  <Download className="mr-2 h-4 w-4" />
                                  JSON
                                </Button>
                              ) : null}

                              {selectedTaskCurrentDownloadFiles.html ? (
                                <Button
                                  type="button"
                                  variant="outline"
                                  className="h-9 w-full justify-center rounded-xl"
                                  onClick={() =>
                                    downloadGroup(selectedTask.id, [selectedTaskCurrentDownloadFiles.html])
                                  }
                                >
                                  <Download className="mr-2 h-4 w-4" />
                                  HTML
                                </Button>
                              ) : null}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ) : null}

                </div>
              )}
            </CardContent>
          </Card>
        </div>
        {profile === "technical" && (
          <article className="mt-6">
            <Card className="rounded-[2rem] border-primary">
              <CardHeader className="pb-4">
                <div className="flex items-start gap-3">
                  <div>
                    <CardTitle className="text-lg text-slate-950 bg-color-primary items-center flex text-white new-rounded py-3 px-4">
                      <Cpu className="h-6 w-6 mr-2" />
                        Información del procesamiento
                    </CardTitle>
                    <CardDescription className="mt-1 text-slate-600">
                      Seguimiento técnico y registro de ejecución de la tarea seleccionada.
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>

              <CardContent>
                {!selectedTask ? (
                  <div className="rounded-[1.5rem] border border-dashed border-slate-300 bg-slate-50 px-6 py-10 text-center">
                    <p className="text-sm font-medium text-slate-700">
                      Selecciona una tarea para ver la información del procesamiento.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-slate-900">
                          Tarea seleccionada
                        </p>
                        <p className="text-sm break-all text-slate-500">
                          ID: {selectedTask.id}
                        </p>
                      </div>

                      <div className="flex items-center gap-2">
                        {canDownloadProcessingLog ? (
                          <Button
                            type="button"
                            variant="outline"
                            className="h-10 w-10 rounded-xl p-0"
                            onClick={() => downloadLog(selectedTask.id)}
                            disabled={loadingLogId === selectedTask.id}
                            aria-label="Descargar información del procesamiento"
                            title="Descargar información del procesamiento"
                          >
                            {loadingLogId === selectedTask.id ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Download className="h-4 w-4" />
                            )}
                          </Button>
                        ) : null}

                        <Button
                          type="button"
                          variant="outline"
                          className="h-10 rounded-xl px-4"
                          onClick={() => toggleLog(selectedTask.id)}
                          disabled={loadingLogId === selectedTask.id}
                        >
                          {showLogByTask[selectedTask.id] ? "Ocultar" : "Mostrar"}
                        </Button>
                      </div>
                    </div>
                    {showLogByTask[selectedTask.id] ? (
                      logsByTask[selectedTask.id] !== undefined ? (
                        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-slate-950 px-4 py-3 shadow-inner">
                          <div
                            ref={logScrollRef}
                            className="max-h-[260px] overflow-auto rounded-xl"
                          >
                            <pre className="whitespace-pre-wrap break-words text-xs leading-6 text-slate-100">
                              {logsByTask[selectedTask.id] || "Registro vacío."}
                            </pre>
                          </div>
                        </div>
                      ) : (
                        <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-5 text-sm text-slate-500">
                          Cargando información del procesamiento...
                        </div>
                      )
                    ) : (
                      <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-5 text-sm text-slate-500">
                        Pulsa en “Mostrar” para ver el registro de ejecución.
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </article>
        )}
        
      </section>
      <footer className="mt-2 pt-6 pb-2 color-primary">
          <div className="mx-auto max-w-5xl px-4 text-center">
            <p className="mx-auto max-w-5xl color-primary text-sm">
              Aiuda se desarrolla en el marco de Labs UniversitarIA, iniciativa de colaboración interuniversitaria
              impulsada por la DIPyC de la Secretaría General Iberoamericana (SEGIB), junto con la Universidade da Coruña,
              la Universidad de Chile, la Universidad Tecnológica del Uruguay, la Universidad de Buenos Aires y la Universidade
              Federal do Rio de Janeiro, con el apoyo de la Agencia Española de Cooperación Internacional para el Desarrollo (AECID).
            </p>
          </div>
          <div className="mt-4 bg-color-primary row p-4 flex flex-col md:flex-row gap-10 pb-8 items-center justify-center">
            <div className="md:w-1/5 flex flex-col gap-3 md:items-center">
              <img src={AIUDA_NEGATIVE_LOGOS_SRC} alt="Aiuda"  className="logo-footer1"/>
              <img src={getPublicAssetUrl("assets/logos/universitariaia.png")} alt="Universitaria IA" className="logo-footer2"/>
            </div>
            <div className="md:w-1/3 flex flex-col gap-3">
              <h4 className="text-white">Organizado por:</h4>
              <img src={getPublicAssetUrl("assets/logos/logos.png")} alt="" />
            </div>
            <div className="md:w-1/4 flex flex-col gap-3">
              <h4 className="text-white">Con el apoyo de:</h4>
              <img src={getPublicAssetUrl("assets/logos/logo_aecid.png")} alt="AECID" className="logo-footer4"/>
            </div>
          </div>
          
      </footer>
    </div>
  )
}