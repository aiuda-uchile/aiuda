import { useEffect, useMemo, useRef, useState } from "react"
import {
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  Clock3,
  Cpu,
  Download,
  FileAudio,
  FileText,
  Filter,
  Loader2,
  Mail,
  Mic,
  RefreshCw,
  ScanSearch,
  Upload,
  Video,
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

const TARGET_LANGS = [
  { code: "es", label: "Español", icon: "🇪🇸" },
  { code: "en", label: "Inglés", icon: "🇬🇧" },
  { code: "pt", label: "Portugués", icon: "🇧🇷" },
  { code: "gl", label: "Gallego", icon: "/galicia-icon.png" },
]

const LANGUAGE_META = {
  es: { label: "Español", icon: "🇪🇸" },
  en: { label: "Inglés", icon: "🇬🇧" },
  pt: { label: "Portugués", icon: "🇧🇷" },
  gl: { label: "Gallego", icon: "/galicia-icon.png" },
}


const FOOTER_LOGOS_SRC = "/aluda-footer.png"
const ALUDA_LOGOS_SRC = "/assets/iconos/aiuda-logo.png"

const TASKS_PER_PAGE = 6

const INITIAL_FORM = {
  mode: "multimedia",
  mediaType: "video",
  email: "joaquim.demoura@udc.es",
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
  if (taskType === "video") return "Vídeo"
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
        badge: "border-sky-200 bg-sky-50 text-sky-700",
        bar: "bg-sky-500",
        icon: Loader2,
      }
    case "finished":
      return {
        label: "Finalizada",
        badge: "border-emerald-200 bg-emerald-50 text-emerald-700",
        bar: "bg-emerald-500",
        icon: CheckCircle2,
      }
    case "error":
      return {
        label: "Con error",
        badge: "border-red-200 bg-red-50 text-red-700",
        bar: "bg-red-500",
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
    if (mediaType === "video") return "video/*"
    return "audio/*"
  }
  return ".pdf,.ppt,.pptx,.doc,.docx"
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
    gl: "/galicia-icon.png",
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

function MetricCard({ title, value, icon: Icon, tone = "slate" }) {
  const tones = {
    slate: "from-slate-900 to-slate-700 text-white",
    blue: "from-sky-600 to-blue-700 text-white",
    green: "from-emerald-600 to-emerald-700 text-white",
    amber: "from-amber-500 to-orange-600 text-white",
    rose: "from-rose-500 to-red-600 text-white",
  }

  return (
    <div className="rounded-[1.6rem] border border-white/70 bg-white/85 p-2 shadow-lg shadow-slate-200/60 backdrop-blur">
      <div className={`rounded-[1.2rem] bg-gradient-to-br p-4 ${tones[tone]}`}>
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm opacity-90">{title}</p>
            <p className="mt-2 text-3xl font-semibold tracking-tight">{value}</p>
          </div>
          <div className="rounded-2xl bg-white/15 p-3">
            <Icon className="h-5 w-5" />
          </div>
        </div>
      </div>
    </div>
  )
}

function PipelineMini({ task }) {
  const status = task?.status
  const steps = [
    { key: "uploaded", label: "Enviado" },
    { key: "queued", label: "En cola" },
    { key: "engine", label: "ALUDA" },
    { key: "ready", label: "Listo" },
    { key: "notified", label: "Avisado" },
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
          className="pointer-events-none absolute left-[10%] top-5 hidden h-1 rounded-full bg-sky-400 md:block"
          style={{
            width: `calc(80% * ${
              activeConnectorCount / Math.max(steps.length - 1, 1)
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
                  className={`relative z-10 flex h-9 w-9 items-center justify-center rounded-full border text-xs font-semibold ${
                    active
                      ? "border-sky-600 bg-sky-600 text-white"
                      : "border-slate-300 bg-white text-slate-500"
                  }`}
                >
                  {idx + 1}
                </div>
                <p className="text-center text-[11px] leading-4 text-slate-600">
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

    if (!selectedFile) {
      setUiError("Selecciona un archivo antes de enviar el trabajo al engine.")
      return
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

    setSubmitting(true)
    setUiError("")

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
      setForm((prev) => ({
        ...INITIAL_FORM,
        email: prev.email,
      }))

      const fileInput = document.getElementById("aluda-file-input")
      if (fileInput) fileInput.value = ""
    } catch (error) {
      setUiError(error.message || "Error creando la tarea.")
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
        [taskId]: `Error cargando la información del procesamiento: ${
          error.message || "desconocido"
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
        [taskId]: `Error cargando la información del procesamiento: ${
          error.message || "desconocido"
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
      video: null,
    }
  }

  return {
    txt: findVariantOutput(outputs, key, "txt"),
    srt: findVariantOutput(outputs, key, "srt"),
    vtt: findVariantOutput(outputs, key, "vtt"),
    json: selectedTaskCurrentJsonFile.filename,
    video: findSubtitledVideoOutput(outputs, key),
  }
}, [selectedTask, selectedTaskCurrentJsonFile])


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
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_#dbeafe,_transparent_22%),radial-gradient(circle_at_top_right,_#dcfce7,_transparent_20%),linear-gradient(to_bottom,_#f8fafc,_#eef2ff)]">
      <div className="mx-auto max-w-7xl px-4 py-8 md:px-6 lg:px-8">
        <div className="mb-8 overflow-hidden rounded-[2rem] border border-white/70 bg-white/85 p-6 shadow-xl shadow-slate-200/60 backdrop-blur md:p-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="max-w-3xl">
              <div className="mb-4">
                <img
                  src={ALUDA_LOGOS_SRC}
                  alt="ALUDA"
                  className="h-14 w-auto object-contain md:h-16"
                />
              </div>

        <p className="text-base leading-7 text-slate-600">
          ALUDA utiliza inteligencia artificial para ayudar al profesorado a crear contenidos accesibles y multilingües a partir de audio, vídeo y documentos.
        </p>
    </div>

    <div className="flex shrink-0">
      <Button
        variant="outline"
        onClick={() => fetchTasks()}
        disabled={loadingTasks}
        className="h-11 rounded-xl border-slate-300 bg-white px-5"
      >
        {loadingTasks ? (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        ) : (
          <RefreshCw className="mr-2 h-4 w-4" />
        )}
        Actualizar
      </Button>
    </div>
  </div>
</div>

 

{uiError ? (
  <div className="mb-6 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 shadow-sm">
    {uiError}
  </div>
) : null}

        <div className="mb-8 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
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

        <div className="grid gap-6 xl:grid-cols-[420px_minmax(0,1fr)_360px]">
          <Card className="rounded-[2rem] border-white/70 bg-white/85 shadow-xl shadow-slate-200/60 backdrop-blur">
            <CardHeader className="pb-4">
              <div className="flex items-start gap-3">
                <div className="rounded-2xl bg-slate-900 p-3 text-white">
                  <Upload className="h-5 w-5" />
                </div>
                <div>
                  <CardTitle className="text-xl text-slate-950">
                    Nueva tarea
                  </CardTitle>
                  <CardDescription className="mt-1 text-slate-600">
                    {/*Sube un recurso pedagógico y déjalo en cola para el engine.*/}
                  </CardDescription>
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
                      className={`rounded-2xl border px-4 py-4 text-left transition ${
                        form.mode === "multimedia"
                          ? "border-sky-200 bg-sky-50 shadow-sm"
                          : "border-slate-200 bg-white"
                      }`}
                    >
                      <div className="mb-2 flex items-center gap-2">
                        <Video className="h-4 w-4 text-slate-700" />
                        <span className="text-sm font-semibold text-slate-900">
                          Multimedia
                        </span>
                      </div>
                      <p className="text-xs text-slate-500">
                        Subtitulado, transcripción, traducción y extracción de audio.
                      </p>
                    </button>

                    <button
                      type="button"
                      onClick={() => handleModeChange("documental")}
                      className={`rounded-2xl border px-4 py-4 text-left transition ${
                        form.mode === "documental"
                          ? "border-emerald-200 bg-emerald-50 shadow-sm"
                          : "border-slate-200 bg-white"
                      }`}
                    >
                      <div className="mb-2 flex items-center gap-2">
                        <FileText className="h-4 w-4 text-slate-700" />
                        <span className="text-sm font-semibold text-slate-900">
                          Accesibilidad
                        </span>
                      </div>
                      <p className="text-xs text-slate-500">
                        PDF/PPT para revisión de color, legibilidad y redacción.
                      </p>
                    </button>
                  </div>
                </div>

                {form.mode === "multimedia" ? (
                  <div className="space-y-2">
                    <Label>Tipo de recurso:</Label>
                    <Select value={form.mediaType} onValueChange={handleMediaTypeChange}>
                    <SelectTrigger className="h-12 rounded-xl border-slate-300 bg-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent position="popper" side="right" align="start" sideOffset={8}>
                      <SelectItem value="video">Vídeo</SelectItem>
                      <SelectItem value="audio">Audio</SelectItem>
                    </SelectContent>
                  </Select>
                  </div>
                ) : null}

                <div className="space-y-2">
                  <Label htmlFor="aluda-file-input">Archivo:</Label>

                  <input
                    id="aluda-file-input"
                    type="file"
                    accept={getAcceptForForm(form.mode, form.mediaType)}
                    onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
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
                    }}
                    className={`flex cursor-pointer items-center justify-between rounded-2xl border px-4 py-3 transition ${
                      isDraggingFile
                        ? "border-sky-400 bg-sky-50"
                        : "border-slate-300 bg-white hover:bg-slate-50"
                    }`}
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-slate-900">
                        {selectedFile ? selectedFile.name : "Seleccionar archivo"}
                      </p>
                      <p className="text-xs text-slate-500">
                        {selectedFile
                          ? "Pulsa o arrastra otro archivo para cambiarlo"
                          : "Haz clic o arrastra aquí tu archivo"}
                      </p>
                    </div>

                    <div className="ml-4 shrink-0 rounded-xl bg-slate-900 px-3 py-2 text-sm font-medium text-white">
                      Examinar
                    </div>
                  </label>

                  <p className="text-xs text-slate-500">
                    {form.mode === "multimedia"
                      ? form.mediaType === "video"
                        ? "Formatos de vídeo para subtitulado, transcripción y traducción."
                        : "Formatos habituales: MP3, WAV, M4A y OGG."
                      : "PDF o presentaciones para evaluación de accesibilidad."}
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">E-mail:</Label>
                  <Input
                    id="email"
                    type="email"
                    className="h-12 rounded-xl border-slate-300 bg-white"
                    value={form.email}
                    onChange={(e) =>
                      setForm((prev) => ({ ...prev, email: e.target.value }))
                    }
                    placeholder="nombre@universidad.es"
                  />
                  <p className="text-xs text-slate-500">
                    Usaremos este correo para enviarte el identificador de la tarea y avisarte cuando finalice la tarea.
                  </p>
                </div>

              <div className="space-y-2">
              <Label htmlFor="notes">Observaciones:</Label>
              <Textarea
                id="notes"
                rows={4}
                className="rounded-xl border-slate-300 bg-white"
                value={form.notes}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, notes: e.target.value }))
                }
                placeholder="Ej.: priorizar subtítulos, revisar especialmente la traducción al gallego, etc."
              />
              <p className="text-xs text-slate-500">
                Opcional. Escribe aquí cualquier contexto o instrucción relevante para esta tarea.
              </p>
            </div>

            <Button
              className="h-12 w-full rounded-xl bg-slate-900 text-white hover:bg-slate-800"
              type="submit"
              disabled={submitting}
            >
              {submitting ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Upload className="mr-2 h-4 w-4" />
              )}
              Enviar tarea
            </Button>

            <Separator />

            <div className="space-y-3">
              <p className="text-sm font-medium text-slate-900">
                Qué hará ALUDA con tu archivo
              </p>

                  <div className="space-y-3 rounded-2xl bg-slate-50 p-4">
                    
{form.mode === "multimedia" ? (
  <>
    {form.mediaType === "video" ? (
      <div className="flex items-center justify-between rounded-xl bg-white px-3 py-3">
        <div>
          <Label>Subtítulos del vídeo</Label>
          <p className="text-xs text-slate-500">
            Genera subtítulos sincronizados para facilitar la visualización, revisión y reutilización del contenido.
          </p>
        </div>
        <Switch
          checked={form.options.subtitles}
          onCheckedChange={(v) => setOption("subtitles", v)}
        />
      </div>
    ) : null}


    <div className="flex items-center justify-between rounded-xl bg-white px-3 py-3">
      <div>
        <Label>Traducción a otros idiomas</Label>
        <p className="text-xs text-slate-500">
          Crea versiones traducidas en los idiomas seleccionados para ampliar el alcance del material.
        </p>
      </div>
      <Switch
        checked={form.options.translation}
        onCheckedChange={(v) => setOption("translation", v)}
      />
    </div>

    {form.mediaType === "video" ? (
      <div className="flex items-center justify-between rounded-xl bg-white px-3 py-3">
        <div>
          <Label>Versión en texto</Label>
          <p className="text-xs text-slate-500">
            Convierte el vídeo en texto para consulta, edición o descarga.
          </p>
        </div>
        <Switch
          checked={form.options.extract_audio}
          onCheckedChange={(v) => setOption("extract_audio", v)}
        />
      </div>
    ) : null}
  </>
) : (
  <>
    <div className="flex items-center justify-between rounded-xl bg-white px-3 py-3">
      <div>
        <Label>Evaluación de accesibilidad</Label>
        <p className="text-xs text-slate-500">
          Activa el análisis documental.
        </p>
      </div>
      <Switch
        checked={form.options.accessibility}
        onCheckedChange={(v) => setOption("accessibility", v)}
      />
    </div>

    <div className="grid gap-3 md:grid-cols-2">
      <div className="flex items-center justify-between rounded-xl bg-white px-3 py-3">
        <div>
          <Label>Daltonismo / color</Label>
          <p className="text-xs text-slate-500">
            Colores problemáticos.
          </p>
        </div>
        <Switch
          checked={form.options.color_blindness}
          onCheckedChange={(v) => setOption("color_blindness", v)}
        />
      </div>

      <div className="flex items-center justify-between rounded-xl bg-white px-3 py-3">
        <div>
          <Label>Tamaño de letra</Label>
          <p className="text-xs text-slate-500">
            Letras demasiado pequeñas.
          </p>
        </div>
        <Switch
          checked={form.options.small_fonts}
          onCheckedChange={(v) => setOption("small_fonts", v)}
        />
      </div>

      <div className="flex items-center justify-between rounded-xl bg-white px-3 py-3">
        <div>
          <Label>Textos largos</Label>
          <p className="text-xs text-slate-500">
            Fragmentos excesivos.
          </p>
        </div>
        <Switch
          checked={form.options.long_texts}
          onCheckedChange={(v) => setOption("long_texts", v)}
        />
      </div>

      <div className="flex items-center justify-between rounded-xl bg-white px-3 py-3">
        <div>
          <Label>Problemas de redacción</Label>
          <p className="text-xs text-slate-500">
            Alertas y recomendaciones.
          </p>
        </div>
        <Switch
          checked={form.options.writing_issues}
          onCheckedChange={(v) => setOption("writing_issues", v)}
        />
      </div>
    </div>

    <div className="flex items-center justify-between rounded-xl bg-white px-3 py-3">
      <div>
        <Label>OCR</Label>
        <p className="text-xs text-slate-500">
          Útil para PDF escaneado.
        </p>
      </div>
      <Switch
        checked={form.options.ocr}
        onCheckedChange={(v) => setOption("ocr", v)}
      />
    </div>

    <div className="flex items-center justify-between rounded-xl bg-white px-3 py-3">
      <div>
        <Label>Traducción del documento</Label>
        <p className="text-xs text-slate-500">
          Traducción adicional de salidas textuales.
        </p>
      </div>
      <Switch
        checked={form.options.translation}
        onCheckedChange={(v) => setOption("translation", v)}
      />
    </div>
  </>
)}

<div className="flex items-center justify-between rounded-xl bg-white px-3 py-3">
  <div>
    <Label>Aviso por correo</Label>
    <p className="text-xs text-slate-500">
      Te enviará una notificación cuando el procesamiento haya finalizado.
    </p>
  </div>
  <Switch
    checked={form.options.notify_by_email}
    onCheckedChange={(v) => setOption("notify_by_email", v)}
  />
</div>

                  </div>
                </div>

                <Separator />

                <div className="space-y-4">
                  <div className="space-y-3">
                    <Label>Idiomas disponibles</Label>
                    <div className="grid gap-3">
                      {TARGET_LANGS.map((lang) => {
                        const checked = form.options.target_langs.includes(lang.code)
                        return (
                          <div
                            key={lang.code}
                            className={`flex items-center justify-between rounded-2xl border px-4 py-3 ${
                              checked
                                ? "border-sky-200 bg-sky-50"
                                : "border-slate-200 bg-white"
                            }`}
                          >
                            <div className="flex items-center gap-3">
                              {lang.code === "gl" ? (
                                <img
                                  src={lang.icon}
                                  alt="Gallego"
                                  className="h-6 w-6 rounded-sm object-contain"
                                />
                              ) : (
                                <span className="text-lg leading-none">{lang.icon}</span>
                              )}

                              <div>
                                <p className="text-sm font-medium text-slate-900">
                                  {lang.label}
                                </p>
                                <p className="text-xs text-slate-500">{lang.code}</p>
                              </div>
                            </div>
                            <Switch
                              checked={checked}
                              disabled={!form.options.translation}
                              onCheckedChange={(value) =>
                                toggleTargetLang(lang.code, value)
                              }
                            />
                          </div>
                        )
                      })}
                    </div>
                  </div>
                </div>

              </form>
            </CardContent>
          </Card>

          <Card className="rounded-[2rem] border-white/70 bg-white/85 shadow-xl shadow-slate-200/60 backdrop-blur">
            <CardHeader className="pb-4">
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <div className="rounded-2xl bg-slate-900 p-3 text-white">
                  <Filter className="h-5 w-5" />
                </div>
                <div>
                  <CardTitle className="text-xl text-slate-950">
                    Cola de tareas
                  </CardTitle>
                  <CardDescription className="mt-1 text-slate-600">
                    {/*Seguimiento del buffer, el engine y el estado de entrega.*/}
                  </CardDescription>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
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
                    className={`rounded-full border px-3 py-2 text-sm text-center transition ${
                      filter === item.key
                        ? "border-slate-900 bg-slate-900 text-white"
                        : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>
          </CardHeader>

            <CardContent>
            <div className="mb-4 space-y-2">
              <Label htmlFor="task-search-id">Localizar tarea</Label>
              <Input
                id="task-search-id"
                className="h-11 rounded-xl border-slate-300 bg-white"
                value={searchId}
                onChange={(e) => setSearchId(e.target.value)}
                placeholder="Introduce el identificador que recibiste por e-mail"
              />
              <p className="text-xs text-slate-500">
                Usa este campo para recuperar una tarea concreta y consultar su estado o descargar sus resultados.
              </p>
            </div>

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
                          className={`w-full rounded-2xl border px-4 py-4 text-left transition ${
                            isSelected
                              ? "border-sky-300 bg-sky-50 shadow-sm"
                              : "border-slate-200 bg-white hover:bg-slate-50"
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            <Badge className={`rounded-full px-2.5 py-0.5 ${status.badge}`}>
                              <StatusIcon
                                className={`mr-1.5 h-3.5 w-3.5 ${
                                  task.status === "processing" ? "animate-spin" : ""
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

          <Card className="rounded-[2rem] border-white/70 bg-white/85 shadow-xl shadow-slate-200/60 backdrop-blur">
          <CardHeader className="pb-4">
            <div className="flex items-start gap-3">
              <div className="rounded-2xl bg-slate-900 p-3 text-white">
                <FileText className="h-5 w-5" />
              </div>
              <div>
                <CardTitle className="text-xl text-slate-950">
                  Detalle y resultados
                </CardTitle>
                <CardDescription className="mt-1 text-slate-600">
                  {/* Estado, salidas, notificación y descarga del resultado final. */}
                </CardDescription>
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

                    <h3 className="text-lg font-semibold text-slate-950">
                      {selectedTask.resource || "Tarea"}
                    </h3>
                    <p className="mt-1 text-sm text-slate-500">
                      ID: {selectedTask.id}
                    </p>

                    <div className="mt-4 grid gap-2 text-sm text-slate-600">
                      {selectedTaskMainDate?.value ? (
                        <div className="rounded-xl bg-slate-50 px-3 py-2">
                          <span className="font-medium text-slate-800">
                            {selectedTaskMainDate.label}:
                          </span>{" "}
                          {formatDate(selectedTaskMainDate.value)}
                        </div>
                      ) : null}
                      <div className="rounded-xl bg-slate-50 px-3 py-2">
                        <span className="font-medium text-slate-800">Email:</span>{" "}
                        {selectedTask.email || "-"}
                      </div>
                      <div className="rounded-xl bg-slate-50 px-3 py-2">
                        <span className="font-medium text-slate-800">Notificación:</span>{" "}
                        {getNotificationState(selectedTask)}
                      </div>
                    </div>
                  </div>

                  <div>
                    <p className="mb-2 text-sm font-medium text-slate-900">
                      Flujo del trabajo
                    </p>
                    <PipelineMini task={selectedTask} />
                  </div>

                  {selectedTask.notes ? (
                    <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                      <div className="mb-2 flex items-center gap-2">
                        <FileText className="h-4 w-4 text-slate-500" />
                        <p className="text-xs font-semibold text-slate-500">
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
                        Ver vídeo subtitulado
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
                          Tu navegador no soporta reproducción de vídeo.
                        </video>

                        <div className="mt-3 flex items-center justify-between gap-3">
                          <p className="text-xs text-slate-500">
                            {selectedTaskCurrentJsonFile
                              ? `Subtítulos mostrados en ${selectedTaskCurrentDownloadMeta.label}.`
                              : "Vídeo con subtítulos incrustados."}
                          </p>

                          <Button
                            type="button"
                            variant="outline"
                            className="h-9 rounded-xl"
                            onClick={() => downloadGroup(selectedTask.id, [selectedTaskCurrentVideoFile])}
                          >
                            <Download className="mr-2 h-4 w-4" />
                            Vídeo
                          </Button>
                        </div>
                      </div>
                    </div>
                  ) : null}

                  {selectedTaskAudioFile ? (
                    <div className="space-y-3">
                      <p className="text-sm font-medium text-slate-900">
                        Escuchar resultado
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
                          variant="outline"
                          className="h-9 rounded-xl"
                          onClick={() => downloadGroup(selectedTask.id, [selectedTaskAudioFile])}
                        >
                          <Download className="mr-2 h-4 w-4" />
                          Audio
                        </Button>
                      </div>
                    </div>
                    </div>
                  ) : null}

    {selectedTaskJsonFiles.length > 0 ? (
  <div className="space-y-3">
    <p className="text-sm font-medium text-slate-900">
      Transcripción y traducciones
    </p>

    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
     <div className="mb-3 flex flex-wrap gap-2">
      {selectedTaskJsonFiles.map((item) => (
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
        ) : selectedTaskCurrentJsonCacheKey &&
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
        <span className="leading-none">{selectedTaskCurrentDownloadMeta.icon}</span>
      ) : null}

      <span>
        Descargas en {selectedTaskCurrentDownloadMeta.label}
      </span>
      </div>

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


</div>


      </div>
    </div>
  </div>
) : null}

                </div>
              )}
            </CardContent>
          </Card>
        </div>
        <main>
            <div className="mt-6">
              <Card className="rounded-[2rem] border-white/70 bg-white/85 shadow-xl shadow-slate-200/60 backdrop-blur">
                <CardHeader className="pb-4">
                  <div className="flex items-start gap-3">
                    <div className="rounded-2xl bg-slate-900 p-3 text-white">
                      <Cpu className="h-5 w-5" />
                    </div>
                    <div>
                      <CardTitle className="text-xl text-slate-950">
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
            </div>
        </main>  
        <footer className="mt-10 border-t border-slate-200/80 pt-6 pb-2">
          <div className="mx-auto max-w-5xl px-4 text-center">
            <p className="mx-auto max-w-4xl text-xs leading-6 text-slate-500">
              ALUDA se desarrolla en el marco de Labs UniversitarIA, iniciativa de colaboración interuniversitaria
              impulsada por la DIPyC de la Secretaría General Iberoamericana (SEGIB), junto con la Universidade da Coruña,
              la Universidad de Chile, la Universidad Tecnológica del Uruguay, la Universidad de Buenos Aires y la Universidade
              Federal do Rio de Janeiro, con el apoyo de la Agencia Española de Cooperación Internacional para el Desarrollo (AECID).
            </p>

            <div className="mt-4 flex justify-center">
              <img
                src={FOOTER_LOGOS_SRC}
                alt="Entidades participantes y financiadoras del proyecto"
                className="h-auto w-full max-w-xl object-contain opacity-90"
              />
            </div>
          </div>
        </footer>
      </div>
    </div>
  )
}