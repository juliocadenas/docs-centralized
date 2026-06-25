'use client';
import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const API = 'http://100.105.27.27:9000/v1';
const GRADIO = 'http://100.105.27.27';

interface Tool {
  id: string; name: string; icon: string; desc: string; gradient: string;
  status: 'online' | 'installing' | 'planned'; category: string; equivalent: string;
  url?: string;
}

interface Category {
  id: string; name: string; icon: string; color: string;
}

const CATEGORIES: Category[] = [
  { id: 'home', name: 'Inicio', icon: '🏠', color: '#6366f1' },
  { id: 'video', name: 'Video Generation', icon: '🎬', color: '#3b82f6' },
  { id: 'avatar', name: 'Avatares & Lip-sync', icon: '🎭', color: '#f59e0b' },
  { id: 'music', name: 'Musica & Audio', icon: '🎵', color: '#10b981' },
  { id: 'image', name: 'Imagenes', icon: '🖼️', color: '#a855f7' },
  { id: 'marketing', name: 'Marketing & Copy', icon: '📝', color: '#ef4444' },
  { id: 'effects', name: 'Efectos & Edicion', icon: '⚡', color: '#f97316' },
  { id: 'chat', name: 'Chat IA', icon: '🤖', color: '#8b5cf6' },
];

const TOOLS: Tool[] = [
  { id: 'video-gen', name: 'Wan2GP', icon: '🎬', desc: 'WAN 2.1 - Genera videos tipo Sora desde texto. 480p/720p, 3-10s. Interfaz integrada', gradient: 'from-blue-600 to-cyan-500', status: 'online', category: 'video', equivalent: 'Sora AI / Kling' },
  { id: 'cogvideox', name: 'CogVideoX (THUDM)', icon: '🎥', desc: 'Video generation de alta calidad. El mejor modelo open-source', gradient: 'from-blue-700 to-indigo-500', status: 'planned', category: 'video', equivalent: 'Pika AI', url: `${GRADIO}:7861` },
  { id: 'open-sora', name: 'Open-Sora (HPC-AI Tech)', icon: '🎞️', desc: 'Video generation tipo Sora 100% open source', gradient: 'from-indigo-600 to-violet-500', status: 'planned', category: 'video', equivalent: 'Sora AI' },
  { id: 'hunyuan', name: 'HunyuanVideo (Tencent)', icon: '📹', desc: 'Video fotorrealista de alta calidad', gradient: 'from-sky-600 to-blue-500', status: 'online', category: 'video', equivalent: 'Kling AI', url: `${GRADIO}:8188` },
  { id: 'story-diffusion', name: 'StoryDiffusion', icon: '📖', desc: 'Personajes consistentes -> comic -> video. Ideal para series', gradient: 'from-indigo-500 to-purple-500', status: 'planned', category: 'video', equivalent: 'Series YouTube' },
  { id: 'agentic-video', name: 'Agentic Video (OpenMontage)', icon: '🤖', desc: 'Pipeline completo: LLM genera guion, Flux crea imágenes, TTS narra, música de fondo, Remotion renderiza. Video profesional 100% local', gradient: 'from-violet-600 via-fuchsia-500 to-pink-500', status: 'online', category: 'video', equivalent: 'Pictory / Synthesia / InVideo' },
  { id: 'avatar-gen', name: 'Hallo2 (Fudan)', icon: '🎭', desc: 'Sube foto + audio -> video del avatar hablando', gradient: 'from-amber-500 to-orange-500', status: 'online', category: 'avatar', equivalent: 'HeyGen', url: `${GRADIO}:8070` },
  { id: 'lipsync', name: 'LatentSync (ByteDance)', icon: '👄', desc: 'Sincronizacion labios perfecta con difusion', gradient: 'from-cyan-500 to-blue-500', status: 'online', category: 'avatar', equivalent: 'HeyGen Lip-sync', url: `${GRADIO}:8043` },
  { id: 'live-portrait', name: 'LivePortrait (KwaiVGI)', icon: '🖼️', desc: 'Anima fotos con expresiones faciales naturales', gradient: 'from-pink-500 to-rose-500', status: 'online', category: 'avatar', equivalent: 'HeyGen Express', url: `${GRADIO}:8044` },
  { id: 'musetalk', name: 'MuseTalk (TME)', icon: '🗣️', desc: 'Lip-sync en tiempo real - Pipeline de avatar hablando', gradient: 'from-teal-500 to-emerald-500', status: 'online', category: 'avatar', equivalent: 'HeyGen Live', url: `${GRADIO}:8040` },
  { id: 'digital-human', name: 'Humano Digital', icon: '🧑‍💻', desc: 'Pipeline completo: LLM + TTS + Lip-sync + Animacion', gradient: 'from-emerald-500 to-teal-500', status: 'planned', category: 'avatar', equivalent: 'HeyGen Pro' },
  { id: 'ai-vtuber', name: 'AI VTuber', icon: '🎮', desc: 'VTuber con IA: TTS + Live2D + Stream automatico', gradient: 'from-violet-500 to-fuchsia-500', status: 'planned', category: 'avatar', equivalent: 'VTuber Studio' },
  { id: 'music-gen', name: 'DocuMusic', icon: '🎵', desc: 'ACE-Step, YuE, DiffRhythm - Canciones completas tipo Suno. Interfaz integrada', gradient: 'from-green-500 to-emerald-500', status: 'online', category: 'music', equivalent: 'Suno.AI' },
  { id: 'image-gen', name: 'Image Gen (Flux/SDXL)', icon: '🎨', desc: 'SDXL, Flux - Imagenes fotorrealistas, arte, logos, banners. Interfaz integrada', gradient: 'from-purple-500 to-pink-500', status: 'online', category: 'image', equivalent: 'Midjourney / Freepik' },
  { id: 'comfyui-advanced', name: 'ComfyUI (Avanzado)', icon: '🔧', desc: 'Editor de nodos completo para workflows personalizados', gradient: 'from-fuchsia-500 to-purple-500', status: 'online', category: 'image', equivalent: 'ComfyUI', url: `${GRADIO}:8188` },
  { id: 'marketing-copy', name: 'Copy Publicitario (Llama 3.1)', icon: '📝', desc: 'Anuncios, emails, slogans - Textos persuasivos con IA', gradient: 'from-orange-500 to-red-500', status: 'online', category: 'marketing', equivalent: 'Jasper AI' },
  { id: 'social-post', name: 'Post Redes (Llama 3.1)', icon: '📱', desc: 'Contenido viral para Instagram, TikTok, YouTube, X', gradient: 'from-rose-500 to-pink-500', status: 'online', category: 'marketing', equivalent: 'Buffer AI' },
  { id: 'blog-writer', name: 'Blog Writer (Llama 3.1)', icon: '✍️', desc: 'Articulos SEO completos con keywords y estructura', gradient: 'from-amber-500 to-yellow-500', status: 'online', category: 'marketing', equivalent: 'Copy.ai' },
  { id: 'slogan-gen', name: 'Slogan Generator (Llama 3.1)', icon: '💡', desc: 'Frases pegadizas para tu marca o campana', gradient: 'from-yellow-500 to-amber-500', status: 'online', category: 'marketing', equivalent: 'Branding AI' },
  { id: 'video-effects', name: 'Higgsfield AI', icon: '⚡', desc: 'Motion control, camara, efectos tipo Higgsfield', gradient: 'from-red-500 to-orange-500', status: 'online', category: 'effects', equivalent: 'Higgsfield AI', url: `${GRADIO}:8052` },
  { id: 'image-upscale', name: 'Real-ESRGAN', icon: '🔍', desc: 'Mejora resolucion hasta 4x con upscaling inteligente. Interfaz integrada', gradient: 'from-slate-500 to-gray-500', status: 'online', category: 'effects', equivalent: 'Upscale.media' },
  { id: 'bg-remove', name: 'Rembg', icon: '✂️', desc: 'Elimina fondos automaticamente con IA. Interfaz integrada', gradient: 'from-gray-500 to-zinc-500', status: 'online', category: 'effects', equivalent: 'Remove.bg' },
  { id: 'tts', name: 'Piper TTS', icon: '🎙️', desc: 'Text-to-Speech en español. Rapido en CPU', gradient: 'from-teal-500 to-emerald-500', status: 'online', category: 'chat', equivalent: 'ElevenLabs', url: `${GRADIO}:8010` },
  { id: 'xtts', name: 'XTTS-v2', icon: '🗣️', desc: 'TTS multilingue con clonacion de voz. Sube un audio y clona cualquier voz', gradient: 'from-orange-500 to-red-500', status: 'online', category: 'chat', equivalent: 'ElevenLabs Voice Cloning' },
  { id: 'fish', name: 'Fish Speech', icon: '🐟', desc: 'TTS alternativo con voces naturales. Soporte multilingue', gradient: 'from-blue-500 to-cyan-500', status: 'online', category: 'chat', equivalent: 'PlayHT' },
  { id: 'stt', name: 'Whisper large-v3', icon: '🎤', desc: 'Speech-to-Text OpenAI. Transcribe audio en 100+ idiomas', gradient: 'from-sky-500 to-indigo-500', status: 'online', category: 'chat', equivalent: 'Whisper API', url: `${GRADIO}:8020` },
  { id: 'chat-ai', name: 'AI Chat (Qwen 2.5 + Llama 3.1)', icon: '🤖', desc: 'Asistente local sin limites, zero tokens. Qwen 2.5 (mejor en español) o Llama 3.1', gradient: 'from-violet-500 to-purple-500', status: 'online', category: 'chat', equivalent: 'ChatGPT' },
  { id: 'vision-ai', name: 'Vision IA (Qwen 2.5-VL)', icon: '👁️', desc: 'Analiza imagenes con IA. Sube una foto y preguntale cualquier cosa', gradient: 'from-indigo-500 to-blue-500', status: 'online', category: 'chat', equivalent: 'GPT-4 Vision' },
  { id: 'rag', name: 'Base de Conocimientos (RAG)', icon: '📚', desc: 'Sube documentos y chatea con ellos. Busqueda semantica + IA', gradient: 'from-emerald-500 to-green-500', status: 'online', category: 'chat', equivalent: 'NotebookLM / ChatGPT Files' },
];

// LLM models available in Ollama (IDs must match Ollama tags exactly)
const LLM_MODELS = [
  // Grupo 1: Modelos grandes (alta calidad)
  { id: 'qwen2.5:14b', name: 'Qwen 2.5 14B', desc: 'Mejor calidad, razonamiento avanzado', icon: '🏆' },
  { id: 'gemma2:9b', name: 'Gemma 2 9B', desc: 'Modelo de Google, excelente calidad', icon: '💎' },
  // Grupo 2: Modeles medianos (balance)
  { id: 'qwen2.5:7b', name: 'Qwen 2.5 7B', desc: 'Mejor razonamiento y español', icon: '🧠' },
  { id: 'qwen2.5-coder:7b', name: 'Qwen 2.5 Coder', desc: 'Especializado en programación', icon: '💻' },
  { id: 'llama3.1', name: 'Llama 3.1 8B', desc: 'Rápido y versátil', icon: '🦙' },
  // Grupo 3: Modelos pequeños (ultra-rápido)
  { id: 'llama3.2:3b', name: 'Llama 3.2 3B', desc: 'Ultra-rápido, tareas simples', icon: '⚡' },
];

import { chatCompletions, chatCompletionsStream, getHubStatus, generateSpeech, transcribeAudio, analyzeImage } from '../lib/api';

async function apiChat(messages: {role:string;content:string}[], model='qwen2.5:7b') {
  const res = await chatCompletions(messages as any, model);
  return res.choices?.[0]?.message?.content || 'Sin respuesta del modelo.';
}

// Stream version - calls onToken for each token received
async function apiChatStream(
  messages: {role:string;content:string}[],
  onToken: (fullText: string) => void,
  model='qwen2.5:7b'
): Promise<string> {
  return chatCompletionsStream(
    messages as any,
    (_token, fullText) => onToken(fullText),
    model
  );
}

// Check if Ollama LLM service is online
async function checkLLMStatus(): Promise<'online'|'offline'|'unknown'> {
  try {
    const status = await getHubStatus();
    // services is an array from the Gateway API
    const services = status.services as any;
    const llm = Array.isArray(services)
      ? services.find((s:any) => s.name === 'ollama')
      : (services as any)?.ollama;
    return llm?.status === 'online' ? 'online' : 'offline';
  } catch { return 'unknown'; }
}

/* ── SERVICE LAZY-LOAD ── */
// Maps tool IDs to Gateway service names for auto-start
const SERVICE_MAP: Record<string, string> = {
  'video-gen': 'wan2gp',
  'hunyuan': 'comfyui',
  'avatar-gen': 'hallo2',
  'lipsync': 'latentsync',
  'live-portrait': 'liveportrait',
  'musetalk': 'musetalk',
  'music-gen': 'documusic',
  'image-gen': 'comfyui',
  'video-effects': 'higgsfield',
  'image-upscale': 'upscale',
  'bg-remove': 'rembg',
  'tts': 'piper_tts',
  'omnivoice': 'omnivoice',
  'stt': 'whisper_stt',
};

// Start a service via Gateway API and poll until it's ready
async function startServiceAndWait(
  toolId: string,
  onProgress?: (pct: number, msg: string) => void
): Promise<{ok: boolean; error?: string}> {
  const serviceName = SERVICE_MAP[toolId];
  if (!serviceName) return {ok: true};
  try {
    onProgress?.(5, 'Enviando señal de inicio...');
    const res = await fetch(`${API}/services/${serviceName}/start`, {method: 'POST'});
    if (!res.ok) return {ok: false, error: `Gateway error ${res.status}`};
    const data = await res.json();
    if (data.status === 'already_running') {
      onProgress?.(100, 'Servicio activo');
      return {ok: true};
    }
    const maxAttempts = 30;
    const messages = ['Cargando modelo en GPU...', 'Inicializando servicio...', 'Preparando interfaz...', 'Casi listo...'];
    for (let i = 0; i < maxAttempts; i++) {
      const pct = Math.round(10 + (i / maxAttempts) * 85);
      const msg = messages[Math.min(Math.floor(i / 8), messages.length - 1)];
      onProgress?.(pct, msg);
      await new Promise(r => setTimeout(r, 2000));
      try {
        const statusRes = await fetch(`${API}/status`);
        if (statusRes.ok) {
          const statusData = await statusRes.json();
          const svc = statusData.services?.find((s: any) => s.name === serviceName);
          if (svc?.status === 'online') {
            onProgress?.(100, 'Servicio listo');
            await new Promise(r => setTimeout(r, 1000));
            return {ok: true};
          }
        }
      } catch {}
    }
    return {ok: false, error: 'Timeout: el servicio no respondió en 60 segundos. Puede que la GPU esté ocupada.'};
  } catch (e: any) {
    return {ok: false, error: e.message || 'Connection failed'};
  }
}

function StatusDot({status}:{status:string}) {
  if (status==='online') return <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400 font-semibold"><span className="w-1.5 h-1.5 rounded-full bg-emerald-400"/></span>;
  if (status==='installing') return <span className="inline-flex items-center gap-1 text-[11px] text-amber-400 font-semibold"><span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"/></span>;
  return <span className="inline-flex items-center gap-1 text-[11px] text-gray-500 font-semibold"><span className="w-1.5 h-1.5 rounded-full bg-gray-600"/></span>;
}

/* ── SIDEBAR ── */
function Sidebar({ active, onSelect, collapsed, onToggle }: {
  active: string; onSelect: (id:string, toolId?:string)=>void;
  collapsed:boolean; onToggle:()=>void;
}) {
  return (
    <motion.aside animate={{width: collapsed?64:260}} className="h-screen bg-[#1a1a2e] border-r border-white/5 flex flex-col flex-shrink-0 overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 h-14 border-b border-white/5 flex-shrink-0">
        <button onClick={onToggle} className="text-xl hover:bg-white/5 rounded-lg w-8 h-8 flex items-center justify-center transition">
          {collapsed ? '☰' : '✕'}
        </button>
        {!collapsed && <span className="font-black text-sm bg-gradient-to-r from-purple-400 via-pink-400 to-orange-400 bg-clip-text text-transparent whitespace-nowrap">AI Hub Madrid</span>}
      </div>
      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-2">
        {CATEGORIES.map(cat => {
          const isActive = active === cat.id || (cat.id !== 'home' && active.startsWith(cat.id));
          const tools = TOOLS.filter(t => t.category === cat.id);
          return (
            <div key={cat.id}>
              <button onClick={() => onSelect(cat.id)} className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm transition-all ${isActive ? 'bg-white/8 text-white' : 'text-gray-400 hover:bg-white/4 hover:text-gray-200'}`}>
                <span className="text-lg flex-shrink-0 w-6 text-center">{cat.icon}</span>
                {!collapsed && <span className="whitespace-nowrap font-medium">{cat.name}</span>}
                {!collapsed && cat.id !== 'home' && <span className="ml-auto text-[10px] bg-white/10 px-1.5 py-0.5 rounded-full text-gray-500">{tools.length}</span>}
              </button>
              {/* Sub-items when active and not collapsed */}
              <AnimatePresence>
                {isActive && !collapsed && cat.id !== 'home' && (
                  <motion.div initial={{height:0,opacity:0}} animate={{height:'auto',opacity:1}} exit={{height:0,opacity:0}} className="overflow-hidden">
                    {tools.map(t => (
                      <button key={t.id} onClick={() => onSelect(cat.id, t.id)} className={`w-full flex items-center gap-2 pl-11 pr-4 py-2 text-xs transition-all ${active === t.id ? 'bg-white/6 text-white' : 'text-gray-500 hover:bg-white/3 hover:text-gray-300'}`}>
                        <StatusDot status={t.status}/>
                        <span className="truncate">{t.name}</span>
                      </button>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })}
      </nav>
      {/* Footer */}
      {!collapsed && (
        <div className="px-4 py-3 border-t border-white/5 text-[10px] text-gray-600">
          NAB9 - RTX 5080 16GB - Zero Tokens
        </div>
      )}
    </motion.aside>
  );
}

/* ── SERVICE MANAGER ── */
function ServiceManager({ services, hubData }: { services: any[]; hubData: any }) {
  const [busy, setBusy] = useState<string|null>(null);
  const [msg, setMsg] = useState('');

  const toggleService = async (svc: any) => {
    const action = svc.status === 'online' ? 'stop' : 'start';
    setBusy(svc.name); setMsg('');
    try {
      const res = await fetch(`${API}/services/${svc.name}/${action}`, { method: 'POST' });
      if (!res.ok) throw new Error(`Error ${res.status}`);
      const data = await res.json();
      setMsg(data.message || data.status || `Servicio ${action === 'start' ? 'iniciado' : 'detenido'}`);
      setTimeout(() => setMsg(''), 3000);
    } catch(e:any) {
      setMsg(`❌ ${e.message}`);
    }
    setBusy(null);
  };

  return (
    <div className="mb-8">
      <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
        <span>🎛️</span> Service Manager
        <span className="text-[10px] font-normal text-gray-500">
          ({services.filter(s=>s.status==='online').length} online / {services.length} total)
        </span>
      </h2>
      {msg && <div className="mb-3 text-xs text-cyan-400 bg-cyan-500/10 border border-cyan-500/20 rounded-lg p-2">{msg}</div>}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
        {services.map(s => (
          <div key={s.name} className={`flex items-center justify-between gap-2 border rounded-lg px-3 py-2 ${s.status==='online'?'bg-emerald-500/5 border-emerald-500/20':'bg-white/[0.02] border-white/5'}`}>
            <div className="flex items-center gap-2 min-w-0">
              <StatusDot status={s.status}/>
              <div className="min-w-0">
                <div className="text-xs text-gray-200 truncate">{s.display_name || s.name}</div>
                {s.vram_mb > 0 && <div className="text-[9px] text-gray-600">{(s.vram_mb/1024).toFixed(1)}GB VRAM</div>}
              </div>
            </div>
            {s.always_on ? (
              <span className="text-[9px] text-gray-600 bg-white/5 px-2 py-1 rounded">always-on</span>
            ) : (
              <button
                onClick={() => toggleService(s)}
                disabled={busy === s.name}
                className={`text-[10px] px-2 py-1 rounded font-bold transition disabled:opacity-50 ${s.status==='online'?'bg-red-500/20 text-red-400 hover:bg-red-500/30':'bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30'}`}
              >
                {busy === s.name ? '⏳' : s.status==='online' ? '⏹ Stop' : '▶ Start'}
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── HOME ── */
function GpuMetricBar({label, used, total, unit, color}: {label:string; used:number; total:number; unit:string; color:string}) {
  const pct = total > 0 ? Math.round((used / total) * 100) : 0;
  return (
    <div>
      <div className="flex justify-between items-baseline mb-1">
        <span className="text-[11px] text-gray-500">{label}</span>
        <span className="text-xs font-mono text-gray-300">{used}{unit} / {total}{unit}</span>
      </div>
      <div className="h-2 bg-white/5 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all duration-700`} style={{width: `${pct}%`}}/>
      </div>
    </div>
  );
}

function HomePage({ onSelect }: { onSelect:(id:string)=>void }) {
  const online = TOOLS.filter(t=>t.status==='online').length;
  const installing = TOOLS.filter(t=>t.status==='installing').length;
  const [hubData, setHubData] = useState<any>(null);
  const [loadingStatus, setLoadingStatus] = useState(true);

  useEffect(() => {
    let mounted = true;
    const fetchData = async () => {
      try {
        const status = await getHubStatus();
        if (mounted) { setHubData(status); setLoadingStatus(false); }
      } catch { if (mounted) setLoadingStatus(false); }
    };
    fetchData();
    const interval = setInterval(fetchData, 5000); // Refresh every 5s
    return () => { mounted = false; clearInterval(interval); };
  }, []);

  const gpu = hubData?.gpu;
  const services = hubData?.services;
  const servicesArray = Array.isArray(services) ? services : Object.entries(services || {}).map(([k,v]:[string,any]) => ({name:k, ...v}));
  const activeServices = servicesArray.filter((s:any) => s.status === 'online').length;
  const servicesSummary = hubData?.services_summary;

  // Normalize GPU data - handle multiple field name formats from Gateway
  const totalVram = gpu?.total_vram_mb ?? gpu?.vram_total_mb ?? 16384;
  const usedVram = gpu?.used_vram_mb ?? gpu?.vram_used_mb ?? 0;
  const gpuOnline = totalVram > 0 && usedVram !== null;
  // Estimate used VRAM from online services if gateway doesn't report it
  const estimatedVramFromServices = servicesArray
    .filter((s:any) => s.status === 'online' && s.vram_mb > 0)
    .reduce((sum:number, s:any) => sum + (s.vram_mb || 0), 0);
  const effectiveUsedVram = usedVram || estimatedVramFromServices;

  return (
    <div className="p-8 max-w-6xl">
      <div className="mb-10">
        <h1 className="text-3xl font-black text-white mb-2">Bienvenido a AI Hub Madrid</h1>
        <p className="text-gray-400 text-sm">Tu estudio de creacion con IA — Videos, avatares, musica, imagenes. Todo local, zero tokens.</p>
      </div>

      {/* GPU Live Dashboard */}
      <div className="bg-gradient-to-br from-[#1a1a2e] to-[#16213e] border border-white/10 rounded-2xl p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            <span className="text-lg">🎮</span> GPU Status - RTX 5080
            {loadingStatus && <span className="text-[10px] text-gray-500 animate-pulse ml-2">cargando...</span>}
          </h2>
          <span className={`text-[10px] px-2 py-1 rounded-full font-bold ${gpuOnline ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
            {gpuOnline ? '● ONLINE' : '● OFFLINE'}
          </span>
        </div>
        {gpuOnline ? (
          <div className="space-y-3">
            <GpuMetricBar
              label="VRAM"
              used={Math.round(effectiveUsedVram / 1024)}
              total={Math.round(totalVram / 1024)}
              unit="GB"
              color="bg-gradient-to-r from-emerald-500 to-teal-400"
            />
            {(gpu?.temperature !== undefined || gpu?.temperature_c !== undefined) && (
              <div className="flex items-center justify-between">
                <span className="text-[11px] text-gray-500">🌡️ Temperatura</span>
                <span className={`text-xs font-mono font-bold ${(gpu.temperature ?? gpu.temperature_c ?? 0) > 80 ? 'text-red-400' : (gpu.temperature ?? gpu.temperature_c ?? 0) > 65 ? 'text-amber-400' : 'text-emerald-400'}`}>
                  {gpu.temperature ?? gpu.temperature_c}°C
                </span>
              </div>
            )}
            {(gpu?.gpu_utilization !== undefined || gpu?.utilization_pct !== undefined) && (
              <GpuMetricBar
                label="⚡ Uso GPU"
                used={gpu.gpu_utilization ?? gpu.utilization_pct ?? 0}
                total={100}
                unit="%"
                color="bg-gradient-to-r from-blue-500 to-cyan-400"
              />
            )}
            {effectiveUsedVram > 0 && servicesArray.some((s:any) => s.status === 'online' && s.vram_mb > 0) && (
              <div className="mt-3 pt-3 border-t border-white/5">
                <p className="text-[10px] text-gray-600 mb-2">VRAM por servicio activo:</p>
                <div className="flex flex-wrap gap-1.5">
                  {servicesArray.filter((s:any) => s.status === 'online' && s.vram_mb > 0).map((s:any) => (
                    <span key={s.name} className="text-[10px] bg-white/5 px-2 py-0.5 rounded-full text-gray-400">
                      {s.display_name || s.name}: {(s.vram_mb / 1024).toFixed(1)}GB
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <p className="text-xs text-gray-600 py-4 text-center">Servidor NAB9 no responde. Verificando conexión...</p>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-10">
        <div className="bg-white/[0.03] border border-white/5 rounded-xl p-5">
          <div className="text-3xl font-black text-emerald-400">{online}</div>
          <div className="text-xs text-gray-500 mt-1">Herramientas activas</div>
        </div>
        <div className="bg-white/[0.03] border border-white/5 rounded-xl p-5">
          <div className="text-3xl font-black text-cyan-400">{activeServices || '-'}</div>
          <div className="text-xs text-gray-500 mt-1">Servicios en GPU</div>
        </div>
        <div className="bg-white/[0.03] border border-white/5 rounded-xl p-5">
          <div className="text-3xl font-black text-gray-500">{TOOLS.filter(t=>t.status==='planned').length}</div>
          <div className="text-xs text-gray-500 mt-1">Planificadas</div>
        </div>
      </div>

      {/* Service Manager - Start/Stop services */}
      {servicesArray.length > 0 && (
        <ServiceManager services={servicesArray} hubData={hubData} />
      )}

      {/* Quick Access */}
      <h2 className="text-lg font-bold text-white mb-4">Acceso rapido</h2>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {TOOLS.filter(t=>t.status==='online').map(t => (
          <button key={t.id} onClick={()=>onSelect(t.id)} className="flex items-center gap-3 bg-white/[0.03] border border-white/5 rounded-xl p-4 hover:bg-white/[0.06] hover:border-white/10 transition text-left group">
            <span className="text-2xl">{t.icon}</span>
            <div className="min-w-0">
              <div className="text-sm font-semibold text-white truncate">{t.name}</div>
              <div className="text-[10px] text-gray-500">Como {t.equivalent}</div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

/* ── CATEGORY PAGE ── */
function CategoryPage({ catId, onSelect }: { catId:string; onSelect:(id:string)=>void }) {
  const cat = CATEGORIES.find(c=>c.id===catId);
  const tools = TOOLS.filter(t=>t.category===catId);
  if (!cat) return null;
  return (
    <div className="p-8 max-w-6xl">
      <div className="flex items-center gap-3 mb-6">
        <span className="text-3xl">{cat.icon}</span>
        <div>
          <h1 className="text-2xl font-black text-white">{cat.name}</h1>
          <p className="text-xs text-gray-500">{tools.length} herramientas disponibles</p>
        </div>
      </div>
      <div className="space-y-3">
        {tools.map(t => (
          <button key={t.id} onClick={()=>onSelect(t.id)} className="w-full flex items-center gap-4 bg-white/[0.02] border border-white/5 rounded-xl p-4 hover:bg-white/[0.05] hover:border-white/10 transition text-left group">
            <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${t.gradient} flex items-center justify-center text-2xl flex-shrink-0`}>{t.icon}</div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-white">{t.name}</span>
                <StatusDot status={t.status}/>
              </div>
              <p className="text-xs text-gray-500 mt-0.5 truncate">{t.desc}</p>
            </div>
            <div className="text-xs text-gray-600 flex-shrink-0">Como {t.equivalent}</div>
            <span className="text-gray-600 group-hover:text-white transition text-sm flex-shrink-0">→</span>
          </button>
        ))}
      </div>
    </div>
  );
}

/* ── TOOL PAGE ── */
function ToolPage({ toolId, onBack }: { toolId:string; onBack:()=>void }) {
  const tool = TOOLS.find(t=>t.id===toolId);
  const [svcState, setSvcState] = useState<'idle'|'starting'|'ready'|'error'>('idle');
  const [svcError, setSvcError] = useState('');
  const [svcProgress, setSvcProgress] = useState(0);
  const [svcMsg, setSvcMsg] = useState('');

  const doStart = () => {
    setSvcState('starting'); setSvcError(''); setSvcProgress(0); setSvcMsg('');
    startServiceAndWait(toolId, (pct, msg) => {
      setSvcProgress(pct);
      setSvcMsg(msg);
    }).then(result => {
      if (result.ok) setSvcState('ready');
      else { setSvcError(result.error || 'Error desconocido'); setSvcState('error'); }
    });
  };

  useEffect(() => {
    if (!tool || tool.status !== 'online' || !tool.url) return;
    const svcName = SERVICE_MAP[toolId];
    if (!svcName) { setSvcState('ready'); return; }
    doStart();
  }, [toolId]);

  if (!tool) return <div className="p-8 text-gray-500">Herramienta no encontrada</div>;

  return (
    <div className="h-full flex flex-col">
      {/* Toolbar */}
      <div className="flex items-center gap-3 px-6 py-3 border-b border-white/5 bg-[#111122] flex-shrink-0">
        <button onClick={onBack} className="text-xs text-gray-400 hover:text-white transition flex items-center gap-1">← Volver</button>
        <div className="h-4 w-px bg-white/10"/>
        <span className="text-lg">{tool.icon}</span>
        <span className="font-bold text-white text-sm">{tool.name}</span>
        <StatusDot status={tool.status}/>
        <span className="text-[10px] text-gray-600 ml-auto">Como {tool.equivalent}</span>
      </div>
      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {tool.status === 'online' && tool.url ? (
          svcState === 'ready' ? (
            <iframe src={tool.url} className="w-full h-full border-0" allow="microphone; camera"/>
          ) : svcState === 'starting' ? (
            <div className="flex flex-col items-center justify-center h-full text-center p-8">
              <div className="text-6xl mb-4 animate-pulse">{tool.icon}</div>
              <h2 className="text-2xl font-bold text-white mb-2">Iniciando {tool.name}...</h2>
              <p className="text-gray-400 max-w-md mb-2">{svcMsg || 'Cargando el modelo en la GPU del servidor NAB9.'}</p>
              <p className="text-3xl font-black text-cyan-400 mb-4">{svcProgress}%</p>
              <div className="w-64 h-2 bg-white/10 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 rounded-full transition-all duration-500" style={{width: `${svcProgress}%`}}/>
              </div>
              <p className="text-[10px] text-gray-600 mt-4">Esto puede tardar 10-30s dependiendo de la carga de la GPU</p>
            </div>
          ) : svcState === 'error' ? (
            <div className="flex flex-col items-center justify-center h-full text-center p-8">
              <div className="text-6xl mb-4 opacity-50">⚠️</div>
              <h2 className="text-2xl font-bold text-white mb-2">No se pudo iniciar el servicio</h2>
              <p className="text-gray-500 max-w-md mb-4">{svcError}</p>
              <button onClick={doStart} className="px-6 py-2 bg-white/10 rounded-lg text-sm hover:bg-white/20 transition text-white">Reintentar</button>
            </div>
          ) : null
        ) : tool.status === 'online' ? (
          <InlineToolPage tool={tool}/>
        ) : tool.status === 'installing' ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-8">
            <div className="text-6xl mb-4 animate-pulse">{tool.icon}</div>
            <h2 className="text-2xl font-bold text-white mb-2">Instalando en el servidor...</h2>
            <p className="text-gray-400 max-w-md">Este modelo se esta configurando en NAB9. Estara disponible proximamente.</p>
            <div className="mt-6 w-64 h-2 bg-white/10 rounded-full overflow-hidden">
              <motion.div className="h-full bg-gradient-to-r from-amber-500 to-yellow-500 rounded-full" initial={{width:'0%'}} animate={{width:'60%'}} transition={{duration:3, repeat:Infinity, repeatType:'reverse'}}/>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-center p-8">
            <div className="text-6xl mb-4 opacity-30">{tool.icon}</div>
            <h2 className="text-2xl font-bold text-white/40 mb-2">Planificado</h2>
            <p className="text-gray-500 max-w-md">Este modelo esta en la lista de instalacion. Equivalente a {tool.equivalent}.</p>
          </div>
        )}
      </div>
    </div>
  );
}

/* ── INLINE TOOLS ── */
function InlineToolPage({ tool }: { tool:Tool }) {
  switch(tool.id) {
    case 'image-gen': return <ImageGenTool tool={tool}/>;
    case 'marketing-copy': case 'social-post': case 'blog-writer': case 'slogan-gen': return <MarketingTool tool={tool}/>;
    case 'chat-ai': return <ChatTool/>;
    case 'vision-ai': return <VisionTool/>;
    case 'tts': case 'xtts': case 'fish': case 'omnivoice': return <VoiceTool tool={tool}/>;
    case 'stt': return <STTTool/>;
    case 'digital-human': return <DigitalHumanTool/>;
    case 'image-upscale': return <UpscaleTool tool={tool}/>;
    case 'bg-remove': return <BgRemoveTool tool={tool}/>;
    case 'video-gen': return <VideoGenTool tool={tool}/>;
    case 'agentic-video': return <AgenticVideoTool tool={tool}/>;
    case 'music-gen': return <MusicGenTool tool={tool}/>;
    case 'rag': return <RAGTool/>;
    default: return <div className="flex items-center justify-center h-full text-gray-500">Interfaz disponible cuando el servicio este activo.</div>;
  }
}

function ImageGenTool({ tool }: { tool:Tool }) {
  const [prompt, setPrompt] = useState('');
  const [negativePrompt, setNegativePrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [images, setImages] = useState<string[]>([]);
  const [model, setModel] = useState('flux');
  const [width, setWidth] = useState(1024);
  const [height, setHeight] = useState(1024);
  const [steps, setSteps] = useState(20);
  const [cfg, setCfg] = useState(7.0);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const PRESETS = [
    { label: 'Producto', prompt: 'Professional product photography, studio lighting, white background, 8k' },
    { label: 'Logo', prompt: 'Minimalist logo design, vector style, clean lines, modern' },
    { label: 'Banner', prompt: 'Social media banner, vibrant colors, modern design, eye-catching' },
    { label: 'Ilustracion', prompt: 'Digital illustration, artistic style, detailed, colorful, creative' },
  ];

  const generate = async () => {
    if (!prompt.trim()) return;
    setLoading(true); setError(''); setImages([]);
    try {
      const { generateImage } = await import('../lib/api');
      const res = await generateImage({ prompt, model, negative_prompt: negativePrompt||undefined, width, height, steps, cfg });
      const urls = (res.data||[]).map((d:any)=>d.url||(d.b64_json?`data:image/png;base64,${d.b64_json}`:null)).filter(Boolean);
      setImages(urls);
    } catch(e:any) { setError(e.message||'Error. Verifica que ComfyUI este activo.'); }
    setLoading(false);
  };

  return (
    <div className="h-full flex flex-col p-6 max-w-4xl mx-auto overflow-y-auto">
      <h2 className="text-lg font-bold text-white mb-1">{tool.icon} {tool.name}</h2>
      <p className="text-xs text-gray-500 mb-4">Genera imagenes local - zero tokens</p>
      <div className="flex gap-2 mb-3">
        <button onClick={()=>{setModel('flux');setSteps(20);setCfg(7.0);}} className={`px-3 py-1.5 rounded-lg text-xs font-semibold ${model==='flux'?'bg-purple-600 text-white':'bg-white/5 text-gray-400 hover:bg-white/10'}`}>🎨 Flux</button>
        <button onClick={()=>{setModel('sdxl');setSteps(20);setCfg(7.0);}} className={`px-3 py-1.5 rounded-lg text-xs font-semibold ${model==='sdxl'?'bg-purple-600 text-white':'bg-white/5 text-gray-400 hover:bg-white/10'}`}>🎨 SDXL</button>
        <button onClick={()=>{setModel('sdxl-turbo');setSteps(1);setCfg(1.0);}} className={`px-3 py-1.5 rounded-lg text-xs font-semibold ${model==='sdxl-turbo'?'bg-amber-600 text-white':'bg-white/5 text-gray-400 hover:bg-white/10'}`}>⚡ SDXL Turbo (1s)</button>
        <button onClick={()=>{setModel('flux-schnell');setSteps(4);setCfg(0.0);}} className={`px-3 py-1.5 rounded-lg text-xs font-semibold ${model==='flux-schnell'?'bg-orange-600 text-white':'bg-white/5 text-gray-400 hover:bg-white/10'}`}>⚡ FLUX Schnell (4s)</button>
      </div>
      <div className="flex flex-wrap gap-1.5 mb-3">
        {PRESETS.map((p,i)=>(<button key={i} onClick={()=>setPrompt(p.prompt)} className="text-[10px] px-2 py-1 bg-white/5 hover:bg-white/10 border border-white/10 rounded-full text-gray-400 hover:text-white">{p.label}</button>))}
      </div>
      <textarea className="w-full bg-white/5 border border-white/10 rounded-xl p-4 text-white placeholder-gray-600 resize-none h-24 focus:border-purple-500 focus:outline-none text-sm mb-3" placeholder="Describe la imagen..." value={prompt} onChange={e=>setPrompt(e.target.value)}/>
      <button onClick={()=>setShowAdvanced(!showAdvanced)} className="text-xs text-gray-500 hover:text-white mb-3 self-start">{showAdvanced?'Ocultar':'Mostrar'} avanzado</button>
      {showAdvanced && (
        <div className="grid grid-cols-2 gap-3 mb-3 bg-white/[0.02] border border-white/5 rounded-xl p-4">
          <div><label className="text-[10px] text-gray-500 block mb-1">Ancho: {width}px</label><input type="range" min="512" max="1536" step="64" value={width} onChange={e=>setWidth(+e.target.value)} className="w-full accent-purple-500"/></div>
          <div><label className="text-[10px] text-gray-500 block mb-1">Alto: {height}px</label><input type="range" min="512" max="1536" step="64" value={height} onChange={e=>setHeight(+e.target.value)} className="w-full accent-purple-500"/></div>
          <div><label className="text-[10px] text-gray-500 block mb-1">Pasos: {steps}</label><input type="range" min="10" max="50" value={steps} onChange={e=>setSteps(+e.target.value)} className="w-full accent-purple-500"/></div>
          <div><label className="text-[10px] text-gray-500 block mb-1">CFG: {cfg.toFixed(1)}</label><input type="range" min="1" max="20" step="0.5" value={cfg} onChange={e=>setCfg(+e.target.value)} className="w-full accent-purple-500"/></div>
          <div className="col-span-2"><input type="text" className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600" placeholder="Negative prompt..." value={negativePrompt} onChange={e=>setNegativePrompt(e.target.value)}/></div>
        </div>
      )}
      <button onClick={generate} disabled={loading||!prompt.trim()} className={`w-full py-3 rounded-xl font-bold text-sm bg-gradient-to-r ${tool.gradient} disabled:opacity-40 mb-4 text-white`}>{loading?'Generando...':'Generar Imagen'}</button>
      {error && <div className="text-red-400 text-sm mb-3 bg-red-500/10 border border-red-500/20 rounded-lg p-3">{error}</div>}
      {images.length>0 && images.map((url,i)=>(
        <div key={i} className="bg-white/[0.03] border border-white/[0.06] rounded-2xl overflow-hidden mb-3">
          <img src={url} alt={`Gen ${i+1}`} className="w-full h-auto"/>
          <div className="p-3"><a href={url} download={`image-${Date.now()}.png`} className="block text-center px-3 py-2 bg-white/10 rounded-lg text-xs hover:bg-white/20 text-white">Descargar</a></div>
        </div>
      ))}
      {loading && <div className="flex flex-col items-center py-12"><div className="text-5xl mb-3 animate-bounce">🎨</div><p className="text-gray-400 text-sm">Generando con {model.toUpperCase()}...</p></div>}
    </div>
  );
}

function MarketingTool({ tool }: { tool:Tool }) {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState('');
  const sys: Record<string,string> = {
    'marketing-copy': 'Eres un experto en marketing y copywriting. Responde SOLO con el contenido solicitado.',
    'social-post': 'Eres un experto en social media. Genera posts virales con emojis y hashtags.',
    'blog-writer': 'Eres experto escritor de blogs y SEO. Articulos bien estructurados con headings.',
    'slogan-gen': 'Eres experto en branding. Genera 10 slogans creativos y pegadizos.',
  };
  const generate = async () => {
    setLoading(true); setResult('');
    try { const c = await apiChat([{role:'system',content:sys[tool.id]||sys['marketing-copy']},{role:'user',content:prompt}]); setResult(c); } catch{ setResult('Error de conexion con el servidor.'); }
    setLoading(false);
  };
  return (
    <div className="h-full flex flex-col p-6 max-w-4xl mx-auto">
      <h2 className="text-lg font-bold text-white mb-4">{tool.icon} {tool.name}</h2>
      <textarea className="w-full bg-white/5 border border-white/10 rounded-xl p-4 text-white placeholder-gray-600 resize-none h-32 focus:border-purple-500 focus:outline-none text-sm mb-3" placeholder={`Describe lo que necesitas...`} value={prompt} onChange={e=>setPrompt(e.target.value)}/>
      <button onClick={generate} disabled={loading||!prompt} className={`w-full py-3 rounded-xl font-bold text-sm bg-gradient-to-r ${tool.gradient} disabled:opacity-40 transition mb-4 text-white`}>
        {loading ? 'Generando...' : `${tool.icon} Generar`}
      </button>
      <div className="flex-1 overflow-y-auto">
        {result && (
          <div className="p-5 bg-white/[0.03] border border-white/[0.06] rounded-2xl">
            <pre className="text-sm text-gray-200 whitespace-pre-wrap font-sans">{result}</pre>
            <button onClick={()=>navigator.clipboard.writeText(result)} className="mt-4 px-4 py-2 bg-white/10 rounded-lg text-xs hover:bg-white/20 transition text-white">Copiar</button>
          </div>
        )}
      </div>
    </div>
  );
}

const MAX_CONTEXT = 20; // Limit context window sent to LLM

function ChatTool() {
  const [messages, setMessages] = useState<{role:string;content:string}[]>([
    {role:'assistant',content:'👋 Hola! Soy tu IA local (zero tokens). Puedo ayudarte con preguntas, escribir código, marketing, lo que necesites. ¿En qué te ayudo?'}
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState('qwen2.5:7b');
  const [llmStatus, setLlmStatus] = useState<'online'|'offline'|'unknown'|'checking'>('checking');
  const [copiedIdx, setCopiedIdx] = useState<number|null>(null);
  const ref = useRef<HTMLDivElement>(null);

  // Check LLM status on mount and periodically
  useEffect(() => {
    checkLLMStatus().then(s => setLlmStatus(s));
    const interval = setInterval(() => checkLLMStatus().then(s => setLlmStatus(s)), 30000);
    return () => clearInterval(interval);
  }, []);

  const send = async () => {
    if (!input.trim()||loading) return;
    if (llmStatus === 'offline') {
      setMessages(p=>[...p, {
        role:'assistant',
        content:'⚠️ El servicio Ollama está offline (probablemente por la GPU). Cuando el servidor vuelva, podrás chatear normalmente.'
      }]);
      return;
    }
    const userMsg = {role:'user',content:input};
    const allMsgs = [...messages, userMsg];
    setMessages(allMsgs);
    setInput(''); setLoading(true);

    // Add empty assistant message that will be filled by streaming
    setMessages(p=>[...p,{role:'assistant',content:''}]);

    try {
      // Send only last MAX_CONTEXT messages to avoid token limits
      const context = allMsgs.slice(-MAX_CONTEXT);
      await apiChatStream(context, (fullText) => {
        // Update the last message (assistant) with streaming text
        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = {role:'assistant', content: fullText};
          return updated;
        });
        // Auto-scroll while streaming
        if (ref.current) ref.current.scrollTop = ref.current.scrollHeight;
      }, selectedModel);
    } catch(e: any) {
      setMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = {role:'assistant', content:`❌ Error: ${e.message || 'No se pudo conectar con el servidor.'}`};
        return updated;
      });
    }
    setLoading(false);
    setTimeout(()=>ref.current?.scrollTo({top:ref.current.scrollHeight,behavior:'smooth'}),100);
  };

  const clearChat = () => {
    setMessages([{role:'assistant',content:'💬 Conversación limpia. ¿Qué necesitas?'}]);
  };

  const copyMsg = (idx: number, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedIdx(idx);
    setTimeout(()=>setCopiedIdx(null), 2000);
  };

  const activeModel = LLM_MODELS.find(m=>m.id===selectedModel);
  const statusColor = llmStatus==='online'?'text-emerald-400':llmStatus==='offline'?'text-red-400':'text-gray-500';
  const statusText = llmStatus==='online'?'● En línea':llmStatus==='offline'?'● Ollama offline':'● Verificando...';

  return (
    <div className="h-full flex flex-col max-w-4xl mx-auto">
      {/* Top bar: model selector + status + clear */}
      <div className="flex items-center gap-3 px-6 py-3 border-b border-white/5 bg-white/[0.02] flex-wrap">
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">Modelo:</span>
          <div className="flex gap-1 flex-wrap">
            {LLM_MODELS.map(m => (
              <button
                key={m.id}
                onClick={() => setSelectedModel(m.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition flex items-center gap-1.5 ${selectedModel===m.id ? 'bg-indigo-600 text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white'}`}
                title={m.desc}
              >
                <span>{m.icon}</span>
                <span>{m.name}</span>
              </button>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-3 ml-auto">
          <span className={`text-[11px] font-semibold ${statusColor}`}>{statusText}</span>
          <button onClick={clearChat} className="text-[11px] text-gray-500 hover:text-white transition px-2 py-1 rounded hover:bg-white/5" title="Limpiar conversación">🗑️ Limpiar</button>
        </div>
      </div>
      {/* Messages */}
      <div ref={ref} className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((m,i)=>{
          const isUser = m.role==='user';
          return (
            <div key={i} className={`group flex ${isUser?'justify-end':'justify-start'}`}>
              <div className={`max-w-[80%] ${isUser?'items-end':'items-start'} flex flex-col gap-1`}>
                <div className={`px-4 py-3 rounded-2xl text-sm whitespace-pre-wrap break-words ${isUser?'bg-indigo-600/30 text-white rounded-br-md':'bg-white/5 text-gray-200 rounded-bl-md'}`}>{m.content}</div>
                {!isUser && m.content && !m.content.startsWith('❌') && !m.content.startsWith('⚠️') && (
                  <button onClick={()=>copyMsg(i, m.content)} className="text-[10px] text-gray-600 hover:text-white transition opacity-0 group-hover:opacity-100">
                    {copiedIdx===i ? '✓ Copiado' : '📋 Copiar'}
                  </button>
                )}
              </div>
            </div>
          );
        })}
        {loading && messages[messages.length-1]?.role === 'user' && (
          <div className="text-gray-500 text-sm animate-pulse flex items-center gap-2">
            <span>{activeModel?.icon}</span>
            <span>{activeModel?.name} pensando...</span>
            <span className="flex gap-1 ml-1">
              <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{animationDelay:'0ms'}}></span>
              <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{animationDelay:'150ms'}}></span>
              <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{animationDelay:'300ms'}}></span>
            </span>
          </div>
        )}
        {loading && messages[messages.length-1]?.role === 'assistant' && messages[messages.length-1]?.content === '' && (
          <div className="text-gray-500 text-sm animate-pulse flex items-center gap-2">
            <span>{activeModel?.icon}</span>
            <span>Iniciando stream...</span>
          </div>
        )}
      </div>
      {/* Input */}
      <div className="flex gap-2 px-6 pb-6 pt-2">
        <input
          className="flex-1 bg-white/5 border border-white/10 rounded-xl p-3 text-white placeholder-gray-600 focus:border-purple-500 focus:outline-none text-sm disabled:opacity-50"
          placeholder={llmStatus==='offline' ? 'Ollama offline - espera al recovery...' : `Escribe tu mensaje a ${activeModel?.name || 'la IA'}...`}
          value={input}
          onChange={e=>setInput(e.target.value)}
          onKeyDown={e=>e.key==='Enter'&&send()}
          disabled={loading}
        />
        <button onClick={send} disabled={loading||!input.trim()} className="px-6 py-3 rounded-xl font-bold bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed transition text-sm text-white">Enviar</button>
      </div>
    </div>
  );
}

/* ── VOICE TOOL (TTS) ── */
function VoiceTool({ tool }: { tool:Tool }) {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [audioUrl, setAudioUrl] = useState('');
  const [language, setLanguage] = useState('es');
  const [voice, setVoice] = useState('');
  const [error, setError] = useState('');

  const ttsModel = tool.id === 'xtts' ? 'xtts' : tool.id === 'fish' ? 'fish' : tool.id === 'omnivoice' ? 'omnivoice' : 'piper';

  const generate = async () => {
    if (!text.trim()) return;
    setLoading(true); setError(''); setAudioUrl('');
    try {
      const blob = await generateSpeech({
        input: text,
        model: ttsModel,
        language,
        voice: voice || undefined,
      });
      const url = URL.createObjectURL(blob);
      setAudioUrl(url);
    } catch(e: any) {
      setError(e.message || 'Error generando audio');
    }
    setLoading(false);
  };

  return (
    <div className="h-full flex flex-col p-6 max-w-3xl mx-auto">
      <h2 className="text-lg font-bold text-white mb-1">{tool.icon} {tool.name}</h2>
      <p className="text-xs text-gray-500 mb-4">Convierte texto a voz{ttsModel !== 'piper' ? ' con clonacion de voz' : ''}</p>

      <div className="flex gap-3 mb-3">
        <select value={language} onChange={e=>setLanguage(e.target.value)} className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white">
          <option value="es">🇪🇸 Español</option>
          <option value="en">🇬🇧 English</option>
          <option value="fr">🇫🇷 Français</option>
          <option value="de">🇩🇪 Deutsch</option>
          <option value="it">🇮🇹 Italiano</option>
          <option value="pt">🇵🇹 Português</option>
        </select>
        {ttsModel !== 'piper' && (
          <input
            placeholder="Nombre de voz (opcional)..."
            value={voice}
            onChange={e=>setVoice(e.target.value)}
            className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600"
          />
        )}
      </div>

      <textarea
        className="w-full bg-white/5 border border-white/10 rounded-xl p-4 text-white placeholder-gray-600 resize-none h-40 focus:border-purple-500 focus:outline-none text-sm mb-3"
        placeholder="Escribe el texto que quieres convertir a voz..."
        value={text}
        onChange={e=>setText(e.target.value)}
      />
      <button onClick={generate} disabled={loading||!text.trim()} className={`w-full py-3 rounded-xl font-bold text-sm bg-gradient-to-r ${tool.gradient} disabled:opacity-40 transition mb-4 text-white`}>
        {loading ? '🎙️ Generando...' : '🎙️ Generar Audio'}
      </button>
      {error && <div className="text-red-400 text-sm mb-3">❌ {error}</div>}
      {audioUrl && (
        <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-5">
          <p className="text-xs text-gray-500 mb-3">Audio generado:</p>
          <audio controls src={audioUrl} className="w-full"/>
          <a href={audioUrl} download="tts-output.wav" className="mt-3 inline-block px-4 py-2 bg-white/10 rounded-lg text-xs hover:bg-white/20 transition text-white">⬇️ Descargar</a>
        </div>
      )}
    </div>
  );
}

/* ── STT TOOL (Speech-to-Text) ── */
function STTTool() {
  const [transcript, setTranscript] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [fileName, setFileName] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const transcribe = async (file: File) => {
    setLoading(true); setError(''); setTranscript(''); setFileName(file.name);
    try {
      const result = await transcribeAudio({ file, language: 'es' });
      setTranscript(result.text || 'Sin texto reconocido');
    } catch(e: any) {
      setError(e.message || 'Error transcribiendo audio');
    }
    setLoading(false);
  };

  return (
    <div className="h-full flex flex-col p-6 max-w-3xl mx-auto">
      <h2 className="text-lg font-bold text-white mb-1">🎤 Whisper STT</h2>
      <p className="text-xs text-gray-500 mb-4">Transcribe audio a texto en 100+ idiomas</p>

      <div
        onClick={() => inputRef.current?.click()}
        className="border-2 border-dashed border-white/10 rounded-2xl p-12 text-center cursor-pointer hover:border-white/20 transition mb-4"
      >
        <div className="text-5xl mb-3">🎤</div>
        <p className="text-sm text-gray-400">{fileName || 'Click para subir archivo de audio'}</p>
        <p className="text-[10px] text-gray-600 mt-1">MP3, WAV, M4A, FLAC</p>
        <input
          ref={inputRef}
          type="file"
          accept="audio/*"
          className="hidden"
          onChange={e => e.target.files?.[0] && transcribe(e.target.files[0])}
        />
      </div>

      {loading && <div className="text-center text-cyan-400 text-sm animate-pulse">📝 Transcribiendo...</div>}
      {error && <div className="text-red-400 text-sm mb-3">❌ {error}</div>}
      {transcript && (
        <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-5">
          <p className="text-xs text-gray-500 mb-2">Transcripción:</p>
          <p className="text-sm text-gray-200 whitespace-pre-wrap">{transcript}</p>
          <button onClick={()=>navigator.clipboard.writeText(transcript)} className="mt-3 px-4 py-2 bg-white/10 rounded-lg text-xs hover:bg-white/20 transition text-white">📋 Copiar</button>
        </div>
      )}
    </div>
  );
}

/* ── DIGITAL HUMAN TOOL (Full Pipeline) ── */
function DigitalHumanTool() {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState('');
  const [result, setResult] = useState<{text?:string; audio_url?:string}|null>(null);
  const [error, setError] = useState('');
  const [llmModel, setLlmModel] = useState('qwen2.5:7b');
  const [ttsModel, setTtsModel] = useState('piper');

  const generate = async () => {
    if (!prompt.trim()) return;
    setLoading(true); setError(''); setResult(null);
    try {
      setStep('1/3 🧠 Generando texto con IA...');
      const llmRes = await chatCompletions([
        {role:'system', content:'Eres un presentador amable. Responde de forma natural y concisa (max 3 frases). Idioma: español.'},
        {role:'user', content: prompt}
      ], llmModel);
      const generatedText = llmRes.choices?.[0]?.message?.content || '';

      setStep('2/3 🎙️ Convirtiendo a voz...');
      const audioBlob = await generateSpeech({
        input: generatedText,
        model: ttsModel,
        language: 'es',
      });
      const audioUrl = URL.createObjectURL(audioBlob);

      setStep('3/3 ✓ Completo');
      setResult({ text: generatedText, audio_url: audioUrl });
      setStep('');
    } catch(e: any) {
      setError(e.message || 'Error en el pipeline');
    }
    setLoading(false);
  };

  return (
    <div className="h-full flex flex-col p-6 max-w-3xl mx-auto">
      <h2 className="text-lg font-bold text-white mb-1">🧑‍💻 Humano Digital</h2>
      <p className="text-xs text-gray-500 mb-4">Pipeline: IA genera texto → TTS lo narra → (proximo: Lip-sync anima avatar)</p>

      <div className="flex gap-3 mb-3 flex-wrap">
        <select value={llmModel} onChange={e=>setLlmModel(e.target.value)} className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white">
          <option value="qwen2.5:14b">🏆 Qwen 2.5 14B (mejor)</option>
          <option value="gemma2:9b">💎 Gemma 2 9B</option>
          <option value="qwen2.5:7b">🧠 Qwen 2.5 7B</option>
          <option value="qwen2.5-coder:7b">💻 Qwen Coder</option>
          <option value="llama3.1">🦙 Llama 3.1 8B</option>
          <option value="llama3.2:3b">⚡ Llama 3.2 3B (rápido)</option>
        </select>
        <select value={ttsModel} onChange={e=>setTtsModel(e.target.value)} className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white">
          <option value="piper">🎙️ Piper TTS</option>
          <option value="xtts">🗣️ XTTS-v2</option>
          <option value="fish">🐟 Fish Speech</option>
        </select>
      </div>

      <textarea
        className="w-full bg-white/5 border border-white/10 rounded-xl p-4 text-white placeholder-gray-600 resize-none h-28 focus:border-purple-500 focus:outline-none text-sm mb-3"
        placeholder="¿Que quieres que diga tu humano digital?"
        value={prompt}
        onChange={e=>setPrompt(e.target.value)}
      />
      <button onClick={generate} disabled={loading||!prompt.trim()} className="w-full py-3 rounded-xl font-bold text-sm bg-gradient-to-r from-emerald-500 to-teal-500 disabled:opacity-40 transition mb-4 text-white">
        {loading ? step || 'Procesando...' : '🚀 Generar Humano Digital'}
      </button>

      {error && <div className="text-red-400 text-sm mb-3">❌ {error}</div>}
      {result && (
        <div className="space-y-4">
          {result.text && (
            <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-5">
              <p className="text-xs text-gray-500 mb-2">📝 Texto generado:</p>
              <p className="text-sm text-gray-200">{result.text}</p>
            </div>
          )}
          {result.audio_url && (
            <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-5">
              <p className="text-xs text-gray-500 mb-2">🎙️ Audio:</p>
              <audio controls src={result.audio_url} className="w-full"/>
            </div>
          )}
          <div className="bg-amber-500/10 border border-amber-500/20 rounded-2xl p-3 text-center">
            <p className="text-xs text-amber-400">ℹ️ El paso de Lip-sync (video) estara disponible cuando inicies un servicio de avatar</p>
          </div>
        </div>
      )}
    </div>
  );
}

/* ── VISION TOOL (Image Analysis) ── */
function VisionTool() {
  const [imageUrl, setImageUrl] = useState('');
  const [previewUrl, setPreviewUrl] = useState('');
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState('');
  const [error, setError] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const PRESET_PROMPTS = [
    'Describe esta imagen en detalle.',
    '¿Qué texto aparece en esta imagen?',
    'Analiza esta imagen para marketing.',
    'Cuenta cuántos objetos hay.',
    'Extrae todos los datos visibles.',
  ];

  const handleFile = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const dataUrl = e.target?.result as string;
      setPreviewUrl(dataUrl);
      setImageUrl(dataUrl);
    };
    reader.readAsDataURL(file);
  };

  const analyze = async () => {
    if (!imageUrl) { setError('Sube una imagen primero'); return; }
    setLoading(true); setError(''); setResult('');
    try {
      const res = await analyzeImage({
        image_url: imageUrl,
        prompt: prompt || 'Describe esta imagen en detalle.',
        model: 'qwen2.5vl:7b',
      });
      setResult(res.choices?.[0]?.message?.content || 'Sin respuesta.');
    } catch(e: any) {
      setError(e.message || 'Error analizando imagen');
    }
    setLoading(false);
  };

  return (
    <div className="h-full flex flex-col p-6 max-w-4xl mx-auto overflow-y-auto">
      <h2 className="text-lg font-bold text-white mb-1">👁️ Vision IA (Qwen 2.5-VL)</h2>
      <p className="text-xs text-gray-500 mb-4">Sube una imagen y pregúntale cualquier cosa a la IA</p>

      <div className="grid md:grid-cols-2 gap-4 mb-4">
        <div
          onClick={() => inputRef.current?.click()}
          className="border-2 border-dashed border-white/10 rounded-2xl p-8 text-center cursor-pointer hover:border-indigo-500/50 transition min-h-[200px] flex flex-col items-center justify-center"
        >
          {previewUrl ? (
            <img src={previewUrl} alt="preview" className="max-h-48 rounded-lg" />
          ) : (
            <>
              <div className="text-5xl mb-3">🖼️</div>
              <p className="text-sm text-gray-400">Click para subir imagen</p>
              <p className="text-[10px] text-gray-600 mt-1">PNG, JPG, WEBP</p>
            </>
          )}
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={e => e.target.files?.[0] && handleFile(e.target.files[0])}
          />
        </div>

        <div>
          <p className="text-xs text-gray-500 mb-2">Pregunta sugerida:</p>
          <div className="flex flex-wrap gap-1.5 mb-3">
            {PRESET_PROMPTS.map((p, i) => (
              <button
                key={i}
                onClick={() => setPrompt(p)}
                className="text-[10px] px-2 py-1 bg-white/5 hover:bg-white/10 border border-white/10 rounded-full text-gray-400 hover:text-white transition"
              >
                {p}
              </button>
            ))}
          </div>
          <textarea
            className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white placeholder-gray-600 resize-none h-24 focus:border-indigo-500 focus:outline-none text-sm"
            placeholder="Escribe tu pregunta sobre la imagen..."
            value={prompt}
            onChange={e=>setPrompt(e.target.value)}
          />
        </div>
      </div>

      <button
        onClick={analyze}
        disabled={loading || !imageUrl}
        className="w-full py-3 rounded-xl font-bold text-sm bg-gradient-to-r from-indigo-500 to-blue-500 disabled:opacity-40 transition mb-4 text-white"
      >
        {loading ? '👁️ Analizando...' : '👁️ Analizar Imagen'}
      </button>

      {error && <div className="text-red-400 text-sm mb-3">❌ {error}</div>}
      {result && (
        <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-5">
          <p className="text-xs text-gray-500 mb-2">📋 Análisis:</p>
          <p className="text-sm text-gray-200 whitespace-pre-wrap">{result}</p>
          <button
            onClick={()=>navigator.clipboard.writeText(result)}
            className="mt-3 px-4 py-2 bg-white/10 rounded-lg text-xs hover:bg-white/20 transition text-white"
          >
            📋 Copiar
          </button>
        </div>
      )}
    </div>
  );
}

/* ── UPSCALE TOOL (Real-ESRGAN) ── */
function UpscaleTool({ tool }: { tool:Tool }) {
  const [previewUrl, setPreviewUrl] = useState('');
  const [resultUrl, setResultUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [scale, setScale] = useState(2);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    const url = URL.createObjectURL(file);
    setPreviewUrl(url); setResultUrl(''); setError('');
  };

  const doUpscale = async () => {
    if (!inputRef.current?.files?.[0]) return;
    setLoading(true); setError(''); setResultUrl('');
    try {
      const { upscaleImage } = await import('../lib/api');
      const blob = await upscaleImage({ file: inputRef.current.files[0], scale });
      setResultUrl(URL.createObjectURL(blob));
    } catch(e: any) { setError(e.message || 'Error escalando imagen'); }
    setLoading(false);
  };

  return (
    <div className="h-full flex flex-col p-6 max-w-3xl mx-auto overflow-y-auto">
      <h2 className="text-lg font-bold text-white mb-1">{tool.icon} {tool.name}</h2>
      <p className="text-xs text-gray-500 mb-4">Mejora la resolucion de imagenes hasta 4x</p>

      <div className="flex gap-2 mb-3">
        {[2, 3, 4].map(s => (
          <button key={s} onClick={()=>setScale(s)} className={`px-4 py-2 rounded-lg text-xs font-bold ${scale===s?'bg-slate-600 text-white':'bg-white/5 text-gray-400 hover:bg-white/10'}`}>
            {s}x
          </button>
        ))}
      </div>

      <div onClick={()=>inputRef.current?.click()} className="border-2 border-dashed border-white/10 rounded-2xl p-8 text-center cursor-pointer hover:border-white/20 transition mb-4">
        {previewUrl ? <img src={previewUrl} alt="original" className="max-h-48 mx-auto rounded-lg"/> : <>
          <div className="text-5xl mb-3">🔍</div>
          <p className="text-sm text-gray-400">Click para subir imagen</p>
          <p className="text-[10px] text-gray-600 mt-1">PNG, JPG, WEBP</p>
        </>}
        <input ref={inputRef} type="file" accept="image/*" className="hidden" onChange={e=>e.target.files?.[0]&&handleFile(e.target.files[0])}/>
      </div>

      <button onClick={doUpscale} disabled={loading||!previewUrl} className="w-full py-3 rounded-xl font-bold text-sm bg-gradient-to-r from-slate-500 to-gray-500 disabled:opacity-40 mb-4 text-white">
        {loading ? '🔍 Escalando...' : `🔍 Escalar ${scale}x`}
      </button>
      {error && <div className="text-red-400 text-sm mb-3">❌ {error}</div>}
      {resultUrl && (
        <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-4">
          <p className="text-xs text-gray-500 mb-3">Resultado:</p>
          <img src={resultUrl} alt="upscaled" className="w-full rounded-lg mb-3"/>
          <a href={resultUrl} download="upscaled.png" className="inline-block px-4 py-2 bg-white/10 rounded-lg text-xs hover:bg-white/20 text-white">⬇️ Descargar</a>
        </div>
      )}
    </div>
  );
}

/* ── BG REMOVE TOOL (Rembg) ── */
function BgRemoveTool({ tool }: { tool:Tool }) {
  const [previewUrl, setPreviewUrl] = useState('');
  const [resultUrl, setResultUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [returnMask, setReturnMask] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    const url = URL.createObjectURL(file);
    setPreviewUrl(url); setResultUrl(''); setError('');
  };

  const doRemove = async () => {
    if (!inputRef.current?.files?.[0]) return;
    setLoading(true); setError(''); setResultUrl('');
    try {
      const { removeBackground } = await import('../lib/api');
      const blob = await removeBackground({ file: inputRef.current.files[0], return_mask: returnMask });
      setResultUrl(URL.createObjectURL(blob));
    } catch(e: any) { setError(e.message || 'Error eliminando fondo'); }
    setLoading(false);
  };

  return (
    <div className="h-full flex flex-col p-6 max-w-3xl mx-auto overflow-y-auto">
      <h2 className="text-lg font-bold text-white mb-1">{tool.icon} {tool.name}</h2>
      <p className="text-xs text-gray-500 mb-4">Elimina fondos automaticamente con IA</p>

      <label className="flex items-center gap-2 mb-3 cursor-pointer">
        <input type="checkbox" checked={returnMask} onChange={e=>setReturnMask(e.target.checked)} className="accent-gray-500"/>
        <span className="text-xs text-gray-400">Generar mascara (B/N) en lugar de imagen transparente</span>
      </label>

      <div onClick={()=>inputRef.current?.click()} className="border-2 border-dashed border-white/10 rounded-2xl p-8 text-center cursor-pointer hover:border-white/20 transition mb-4">
        {previewUrl ? <img src={previewUrl} alt="original" className="max-h-48 mx-auto rounded-lg"/> : <>
          <div className="text-5xl mb-3">✂️</div>
          <p className="text-sm text-gray-400">Click para subir imagen</p>
          <p className="text-[10px] text-gray-600 mt-1">PNG, JPG, WEBP</p>
        </>}
        <input ref={inputRef} type="file" accept="image/*" className="hidden" onChange={e=>e.target.files?.[0]&&handleFile(e.target.files[0])}/>
      </div>

      <button onClick={doRemove} disabled={loading||!previewUrl} className="w-full py-3 rounded-xl font-bold text-sm bg-gradient-to-r from-gray-500 to-zinc-500 disabled:opacity-40 mb-4 text-white">
        {loading ? '✂️ Procesando...' : '✂️ Eliminar Fondo'}
      </button>
      {error && <div className="text-red-400 text-sm mb-3">❌ {error}</div>}
      {resultUrl && (
        <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-4" style={{backgroundImage:'url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAJ0lEQVQYV2P89evXfwY0wMjIyIgyMIyMjIyMjIyMjIyMjIyMjIyMjIyMjI8N3T2NAAAAAElFTkSuQmCC")'}}>
          <p className="text-xs text-gray-500 mb-3">Resultado:</p>
          <img src={resultUrl} alt="result" className="w-full rounded-lg mb-3"/>
          <a href={resultUrl} download="no-bg.png" className="inline-block px-4 py-2 bg-white/10 rounded-lg text-xs hover:bg-white/20 text-white">⬇️ Descargar</a>
        </div>
      )}
    </div>
  );
}

/* ── VIDEO GEN TOOL (Wan2GP) ── */
function VideoGenTool({ tool }: { tool:Tool }) {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [videoUrl, setVideoUrl] = useState('');
  const [model, setModel] = useState('wan2.1');
  const [duration, setDuration] = useState(5);
  const [resolution, setResolution] = useState('480p');

  const PRESETS = [
    { label: 'Cinemático', prompt: 'cinematic shot, dramatic lighting, professional film quality' },
    { label: 'Producto', prompt: 'product showcase, rotating display, clean studio background' },
    { label: 'Naturaleza', prompt: 'nature documentary style, beautiful landscape, golden hour' },
    { label: 'Animación', prompt: '3D animation style, smooth motion, vibrant colors' },
  ];

  const generate = async () => {
    if (!prompt.trim()) return;
    setLoading(true); setError(''); setVideoUrl('');
    try {
      const { generateVideo } = await import('../lib/api');
      const res = await generateVideo({ prompt, model, duration_seconds: duration, resolution });
      if (res.url) setVideoUrl(res.url);
      else if (res.video_url) setVideoUrl(res.video_url);
      else if (res.output?.[0]) setVideoUrl(res.output[0]);
      else throw new Error('Respuesta sin URL de video');
    } catch(e:any) { setError(e.message||'Error. Verifica que Wan2GP este activo.'); }
    setLoading(false);
  };

  return (
    <div className="h-full flex flex-col p-6 max-w-4xl mx-auto overflow-y-auto">
      <h2 className="text-lg font-bold text-white mb-1">{tool.icon} {tool.name}</h2>
      <p className="text-xs text-gray-500 mb-4">Genera videos con IA desde texto - zero tokens</p>

      <div className="flex gap-3 mb-3 flex-wrap">
        <select value={model} onChange={e=>setModel(e.target.value)} className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white">
          <option value="wan2.1">🚀 WAN 2.1 (rapido 1.3B)</option>
          <option value="ltx">⚡ LTX Video</option>
          <option value="hunyuan">📹 HunyuanVideo (calidad)</option>
        </select>
        <select value={resolution} onChange={e=>setResolution(e.target.value)} className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white">
          <option value="480p">480p (rapido)</option>
          <option value="720p">720p (lento)</option>
        </select>
        <div className="flex items-center gap-2 bg-white/5 border border-white/10 rounded-lg px-3 py-2">
          <span className="text-xs text-gray-500">Duracion:</span>
          {[3,5,8,10].map(d => (
            <button key={d} onClick={()=>setDuration(d)} className={`text-xs px-2 py-0.5 rounded ${duration===d?'bg-cyan-600 text-white':'text-gray-400 hover:bg-white/10'}`}>{d}s</button>
          ))}
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5 mb-3">
        {PRESETS.map((p,i)=>(
          <button key={i} onClick={()=>setPrompt(p.prompt)} className="text-[10px] px-2 py-1 bg-white/5 hover:bg-white/10 border border-white/10 rounded-full text-gray-400 hover:text-white">{p.label}</button>
        ))}
      </div>

      <textarea className="w-full bg-white/5 border border-white/10 rounded-xl p-4 text-white placeholder-gray-600 resize-none h-28 focus:border-cyan-500 focus:outline-none text-sm mb-3" placeholder="Describe el video que quieres generar..." value={prompt} onChange={e=>setPrompt(e.target.value)}/>

      <button onClick={generate} disabled={loading||!prompt.trim()} className={`w-full py-3 rounded-xl font-bold text-sm bg-gradient-to-r ${tool.gradient} disabled:opacity-40 mb-4 text-white`}>
        {loading?'🎬 Generando video (esto tarda minutos)...':'🎬 Generar Video'}
      </button>
      {error && <div className="text-red-400 text-sm mb-3 bg-red-500/10 border border-red-500/20 rounded-lg p-3">❌ {error}</div>}
      {loading && (
        <div className="flex flex-col items-center py-12">
          <div className="text-5xl mb-3 animate-bounce">🎬</div>
          <p className="text-gray-400 text-sm">Generando con {model}... esto puede tardar varios minutos</p>
          <p className="text-gray-600 text-[10px] mt-2">La GPU procesa frame por frame</p>
        </div>
      )}
      {videoUrl && (
        <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl overflow-hidden">
          <video controls src={videoUrl} className="w-full"/>
          <div className="p-3">
            <a href={videoUrl} download="video.mp4" className="block text-center px-3 py-2 bg-white/10 rounded-lg text-xs hover:bg-white/20 text-white">⬇️ Descargar</a>
          </div>
        </div>
      )}
    </div>
  );
}

/* ── AGENTIC VIDEO TOOL (OpenMontage + Remotion) ── */
function AgenticVideoTool({ tool }: { tool:Tool }) {
  const [topic, setTopic] = useState('');
  const [duration, setDuration] = useState(60);
  const [style, setStyle] = useState('educational');
  const [language, setLanguage] = useState('es');
  const [llmModel, setLlmModel] = useState('qwen2.5:14b');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [jobId, setJobId] = useState('');
  const [status, setStatus] = useState<{progress:number; message:string; status:string; video_url?:string}|null>(null);
  const pollRef = useRef<any>(null);

  const STYLES = [
    { id: 'educational', label: '🎓 Educativo' },
    { id: 'promotional', label: '📢 Promocional' },
    { id: 'documentary', label: '🎙️ Documental' },
    { id: 'storytelling', label: '📖 Narrativa' },
  ];

  const PRESETS = [
    'Introducción a la inteligencia artificial',
    'Los 5 beneficios del ejercicio diario',
    'Historia del espacio en 60 segundos',
    'Cómo funciona el cerebro humano',
    'Tutorial: crear una página web',
    'Resumen de noticias tecnológicas',
  ];

  const start = async () => {
    if (!topic.trim()) return;
    setLoading(true); setError(''); setStatus(null); setJobId('');
    try {
      const { createAgenticVideo } = await import('../lib/api');
      const res = await createAgenticVideo({
        topic,
        duration_seconds: duration,
        style,
        language,
        model: llmModel,
      });
      setJobId(res.job_id);
      setStatus({ progress: 0, message: res.message, status: 'started' });

      pollRef.current = setInterval(async () => {
        try {
          const { getAgenticVideoStatus } = await import('../lib/api');
          const s = await getAgenticVideoStatus(res.job_id);
          setStatus({ progress: s.progress, message: s.message, status: s.status, video_url: s.video_url });
          if (s.status === 'completed' || s.status === 'error') {
            if (pollRef.current) clearInterval(pollRef.current);
            setLoading(false);
          }
        } catch {}
      }, 5000);
    } catch(e: any) {
      setError(e.message || 'Error iniciando pipeline');
      setLoading(false);
    }
  };

  useEffect(() => {
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, []);

  const videoFullUrl = status?.video_url ? `${API.replace('/v1','')}${status.video_url}` : null;

  return (
    <div className="h-full flex flex-col p-6 max-w-4xl mx-auto overflow-y-auto">
      <h2 className="text-lg font-bold text-white mb-1">{tool.icon} {tool.name}</h2>
      <p className="text-xs text-gray-500 mb-4">Pipeline completo: LLM guion → Imágenes IA → Narración TTS → Música → Render. 100% local, zero tokens.</p>

      <div className="bg-violet-500/10 border border-violet-500/20 rounded-xl p-3 mb-4">
        <p className="text-[11px] text-violet-300">
          🤖 Este pipeline usa TODOS los servicios: Ollama (guion), ComfyUI (imágenes), Piper (voz), DocuMusic (música), Remotion (render final).
          Requiere que los servicios estén activos en NAB9.
        </p>
      </div>

      <div className="flex gap-3 mb-3 flex-wrap">
        <select value={style} onChange={e=>setStyle(e.target.value)} className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white">
          {STYLES.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
        </select>
        <select value={language} onChange={e=>setLanguage(e.target.value)} className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white">
          <option value="es">🇪🇸 Español</option>
          <option value="en">🇬🇧 English</option>
        </select>
        <select value={llmModel} onChange={e=>setLlmModel(e.target.value)} className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white">
          <option value="qwen2.5:14b">🏆 Qwen 2.5 14B</option>
          <option value="qwen2.5:7b">🧠 Qwen 2.5 7B</option>
          <option value="llama3.1">🦙 Llama 3.1</option>
        </select>
        <div className="flex items-center gap-2 bg-white/5 border border-white/10 rounded-lg px-3 py-2">
          <span className="text-xs text-gray-500">Duración:</span>
          {[30, 60, 90, 120].map(d => (
            <button key={d} onClick={()=>setDuration(d)} className={`text-xs px-2 py-0.5 rounded ${duration===d?'bg-violet-600 text-white':'text-gray-400 hover:bg-white/10'}`}>{d}s</button>
          ))}
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5 mb-3">
        {PRESETS.map((p, i) => (
          <button key={i} onClick={()=>setTopic(p)} className="text-[10px] px-2 py-1 bg-white/5 hover:bg-white/10 border border-white/10 rounded-full text-gray-400 hover:text-white">{p}</button>
        ))}
      </div>

      <textarea
        className="w-full bg-white/5 border border-white/10 rounded-xl p-4 text-white placeholder-gray-600 resize-none h-24 focus:border-violet-500 focus:outline-none text-sm mb-3"
        placeholder="¿De qué quieres el video? Ej: 'Los beneficios de la meditación diaria'"
        value={topic}
        onChange={e=>setTopic(e.target.value)}
      />

      <button
        onClick={start}
        disabled={loading || !topic.trim()}
        className={`w-full py-3 rounded-xl font-bold text-sm bg-gradient-to-r ${tool.gradient} disabled:opacity-40 mb-4 text-white`}
      >
        {loading ? '🤖 Pipeline en progreso...' : '🚀 Crear Video Agentic'}
      </button>

      {error && <div className="text-red-400 text-sm mb-3 bg-red-500/10 border border-red-500/20 rounded-lg p-3">❌ {error}</div>}

      {status && (
        <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-5 mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-gray-500">Estado del pipeline:</span>
            <span className={`text-xs font-bold ${status.status==='completed'?'text-emerald-400':status.status==='error'?'text-red-400':'text-violet-400'}`}>
              {status.status === 'completed' ? '✅ Completado' : status.status === 'error' ? '❌ Error' : '⚙️ Procesando'}
            </span>
          </div>
          <p className="text-sm text-gray-200 mb-3">{status.message}</p>
          {status.status !== 'completed' && status.status !== 'error' && (
            <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-violet-500 via-fuchsia-500 to-pink-500 rounded-full transition-all duration-500"
                style={{ width: `${status.progress}%` }}
              />
            </div>
          )}
          <p className="text-right text-xs text-gray-600 mt-1">{status.progress}%</p>
          {jobId && <p className="text-[10px] text-gray-600 mt-2">Job ID: <code className="text-gray-500">{jobId}</code></p>}
        </div>
      )}

      {status?.status === 'completed' && videoFullUrl && (
        <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl overflow-hidden">
          <video controls src={videoFullUrl} className="w-full" />
          <div className="p-3 flex gap-2">
            <a href={videoFullUrl} download="agentic-video.mp4" className="flex-1 text-center px-3 py-2 bg-white/10 rounded-lg text-xs hover:bg-white/20 text-white">⬇️ Descargar</a>
            <a href={videoFullUrl} target="_blank" className="flex-1 text-center px-3 py-2 bg-white/10 rounded-lg text-xs hover:bg-white/20 text-white">🔗 Abrir</a>
          </div>
        </div>
      )}

      {loading && (
        <div className="flex flex-col items-center py-8">
          <div className="text-5xl mb-3 animate-spin">🤖</div>
          <p className="text-gray-400 text-sm">El pipeline está trabajando...</p>
          <p className="text-gray-600 text-[10px] mt-2">Generando guion, imágenes, audio y renderizando. Esto puede tardar varios minutos.</p>
        </div>
      )}
    </div>
  );
}

/* ── MUSIC GEN TOOL (DocuMusic) ── */
function MusicGenTool({ tool }: { tool:Tool }) {
  const [prompt, setPrompt] = useState('');
  const [lyrics, setLyrics] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [audioUrl, setAudioUrl] = useState('');
  const [model, setModel] = useState('ace-step');
  const [duration, setDuration] = useState(30);

  const GENRES = ['Pop','Rock','Electronic','Hip-Hop','Jazz','Classical','Reggaeton','Flamenco','Ambient','Lo-Fi'];

  const generate = async () => {
    if (!prompt.trim()) return;
    setLoading(true); setError(''); setAudioUrl('');
    try {
      const { generateAudio } = await import('../lib/api');
      const fullPrompt = lyrics ? `${prompt} | Lyrics: ${lyrics}` : prompt;
      const res = await generateAudio({ prompt: fullPrompt, model, duration_seconds: duration });
      if (res.url) setAudioUrl(res.url);
      else if (res.audio_url) setAudioUrl(res.audio_url);
      else throw new Error('Respuesta sin URL de audio');
    } catch(e:any) { setError(e.message||'Error. Verifica que DocuMusic este activo.'); }
    setLoading(false);
  };

  return (
    <div className="h-full flex flex-col p-6 max-w-4xl mx-auto overflow-y-auto">
      <h2 className="text-lg font-bold text-white mb-1">{tool.icon} {tool.name}</h2>
      <p className="text-xs text-gray-500 mb-4">Genera musica y canciones completas con IA</p>

      <div className="flex gap-3 mb-3 flex-wrap">
        <select value={model} onChange={e=>setModel(e.target.value)} className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white">
          <option value="ace-step">🚀 ACE-Step (rapido 3.5B)</option>
          <option value="yue">🎵 YuE (canciones largas)</option>
          <option value="diffrhythm">🥁 DiffRhythm (ritmico)</option>
        </select>
        <div className="flex items-center gap-2 bg-white/5 border border-white/10 rounded-lg px-3 py-2">
          <span className="text-xs text-gray-500">Duracion:</span>
          {[15,30,60,120].map(d => (
            <button key={d} onClick={()=>setDuration(d)} className={`text-xs px-2 py-0.5 rounded ${duration===d?'bg-emerald-600 text-white':'text-gray-400 hover:bg-white/10'}`}>{d}s</button>
          ))}
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5 mb-3">
        {GENRES.map(g => (
          <button key={g} onClick={()=>setPrompt(prev=>prev?`${prev}, ${g}`:g)} className="text-[10px] px-2 py-1 bg-white/5 hover:bg-white/10 border border-white/10 rounded-full text-gray-400 hover:text-white">{g}</button>
        ))}
      </div>

      <input className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white placeholder-gray-600 text-sm mb-3 focus:border-emerald-500 focus:outline-none" placeholder="Describe la musica (genero, mood, instrumentos)..." value={prompt} onChange={e=>setPrompt(e.target.value)}/>

      <textarea className="w-full bg-white/5 border border-white/10 rounded-xl p-4 text-white placeholder-gray-600 resize-none h-20 focus:border-emerald-500 focus:outline-none text-sm mb-3" placeholder="Letra opcional (una linea por frase)..." value={lyrics} onChange={e=>setLyrics(e.target.value)}/>

      <button onClick={generate} disabled={loading||!prompt.trim()} className={`w-full py-3 rounded-xl font-bold text-sm bg-gradient-to-r ${tool.gradient} disabled:opacity-40 mb-4 text-white`}>
        {loading?'🎵 Generando musica (esto tarda minutos)...':'🎵 Generar Musica'}
      </button>
      {error && <div className="text-red-400 text-sm mb-3 bg-red-500/10 border border-red-500/20 rounded-lg p-3">❌ {error}</div>}
      {loading && (
        <div className="flex flex-col items-center py-12">
          <div className="text-5xl mb-3 animate-bounce">🎵</div>
          <p className="text-gray-400 text-sm">Generando con {model}... paciencia</p>
        </div>
      )}
      {audioUrl && (
        <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-5">
          <p className="text-xs text-gray-500 mb-3">Audio generado:</p>
          <audio controls src={audioUrl} className="w-full"/>
          <a href={audioUrl} download="music.wav" className="mt-3 inline-block px-4 py-2 bg-white/10 rounded-lg text-xs hover:bg-white/20 transition text-white">⬇️ Descargar</a>
        </div>
      )}
    </div>
  );
}

/* ── RAG TOOL (Knowledge Base) ── */
function RAGTool() {
  const [collections, setCollections] = useState<any[]>([]);
  const [selectedCollection, setSelectedCollection] = useState('default');
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState('');
  const [sources, setSources] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [uploadMsg, setUploadMsg] = useState('');
  const [llmModel, setLlmModel] = useState('qwen2.5:7b');
  const [ragHealth, setRagHealth] = useState<'ok'|'not_installed'|'checking'>('checking');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadCollections();
    checkRagHealth();
  }, []);

  const loadCollections = async () => {
    try {
      const res = await fetch(`${API}/rag/collections`);
      if (res.ok) {
        const data = await res.json();
        setCollections(data.collections || []);
      }
    } catch {}
  };

  const checkRagHealth = async () => {
    try {
      const res = await fetch(`${API}/rag/health`);
      const data = await res.json();
      setRagHealth(data.status === 'ok' ? 'ok' : 'not_installed');
    } catch { setRagHealth('not_installed'); }
  };

  const uploadFile = async (file: File) => {
    setUploading(true); setError(''); setUploadMsg('');
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('collection', selectedCollection);
      const res = await fetch(`${API}/rag/upload`, { method: 'POST', body: formData });
      const data = await res.json();
      if (res.ok) {
        setUploadMsg(`✅ ${data.filename}: ${data.chunks_created} fragmentos indexados (${data.total_in_collection} total)`);
        loadCollections();
      } else {
        setError(data.detail || 'Error al subir documento');
      }
    } catch(e: any) {
      setError(e.message || 'Error de conexión');
    }
    setUploading(false);
  };

  const ask = async () => {
    if (!query.trim()) return;
    setLoading(true); setError(''); setAnswer(''); setSources([]);
    try {
      const res = await fetch(`${API}/rag/query`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ query, collection: selectedCollection, model: llmModel })
      });
      const data = await res.json();
      if (res.ok) {
        setAnswer(data.answer);
        setSources(data.sources || []);
      } else {
        setError(data.detail || 'Error en la consulta');
      }
    } catch(e: any) {
      setError(e.message || 'Error de conexión');
    }
    setLoading(false);
  };

  const createCollection = async () => {
    const name = prompt('Nombre de la nueva colección:');
    if (!name) return;
    try {
      await fetch(`${API}/rag/collections`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ name, description: 'Colección personalizada' })
      });
      loadCollections();
      setSelectedCollection(name);
    } catch {}
  };

  if (ragHealth === 'not_installed') {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center">
        <div className="text-6xl mb-4 opacity-50">📚</div>
        <h2 className="text-xl font-bold text-white mb-2">Sistema RAG no instalado</h2>
        <p className="text-gray-500 max-w-md mb-4">
          Ejecuta en el servidor el script de instalación:<br/>
          <code className="text-emerald-400 text-sm">bash _install_rag.sh</code>
        </p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col p-6 max-w-4xl mx-auto overflow-y-auto">
      <h2 className="text-lg font-bold text-white mb-1">📚 Base de Conocimientos (RAG)</h2>
      <p className="text-xs text-gray-500 mb-4">Sube documentos y chatea con ellos. Búsqueda semántica + IA, zero tokens.</p>

      <div className="flex gap-2 mb-4 flex-wrap items-center">
        <select value={selectedCollection} onChange={e=>setSelectedCollection(e.target.value)} className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white">
          <option value="default">📄 default</option>
          {collections.map(c => (
            <option key={c.name} value={c.name}>📄 {c.name} ({c.count} fragmentos)</option>
          ))}
        </select>
        <button onClick={createCollection} className="text-xs px-3 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-gray-400 hover:text-white transition">
          ➕ Nueva colección
        </button>
        <button onClick={()=>inputRef.current?.click()} disabled={uploading} className="text-xs px-4 py-2 bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600/30 border border-emerald-500/20 rounded-lg font-bold transition disabled:opacity-50">
          {uploading ? '⏳ Subiendo...' : '📤 Subir documento'}
        </button>
        <input
          ref={inputRef}
          type="file"
          accept=".txt,.md,.pdf,.json"
          className="hidden"
          onChange={e=>e.target.files?.[0] && uploadFile(e.target.files[0])}
        />
      </div>

      {uploadMsg && <div className="mb-3 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-2">{uploadMsg}</div>}
      {error && <div className="mb-3 text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg p-2">❌ {error}</div>}

      <div className="mb-4 text-[10px] text-gray-600">
        Formatos soportados: TXT, Markdown, PDF, JSON — El texto se divide en fragmentos y se indexa con embeddings
      </div>

      <div className="border-t border-white/5 pt-4">
        <div className="flex gap-2 mb-3">
          <select value={llmModel} onChange={e=>setLlmModel(e.target.value)} className="bg-white/5 border border-white/10 rounded-lg px-2 py-2 text-xs text-white">
            <option value="qwen2.5:14b">🏆 Qwen 14B</option>
            <option value="qwen2.5:7b">🧠 Qwen 7B</option>
            <option value="llama3.1">🦙 Llama 3.1</option>
            <option value="llama3.2:3b">⚡ Llama 3.2</option>
          </select>
          <span className="text-[10px] text-gray-600 self-center ml-auto">
            Colección: {selectedCollection} ({collections.find(c=>c.name===selectedCollection)?.count || 0} fragmentos)
          </span>
        </div>

        <textarea
          className="w-full bg-white/5 border border-white/10 rounded-xl p-4 text-white placeholder-gray-600 resize-none h-24 focus:border-emerald-500 focus:outline-none text-sm mb-3"
          placeholder="Pregunta sobre tus documentos..."
          value={query}
          onChange={e=>setQuery(e.target.value)}
          onKeyDown={e=>e.key==='Enter'&&!e.shiftKey&&(e.preventDefault(),ask())}
        />

        <button onClick={ask} disabled={loading||!query.trim()} className="w-full py-3 rounded-xl font-bold text-sm bg-gradient-to-r from-emerald-500 to-green-500 disabled:opacity-40 mb-4 text-white">
          {loading ? '🔍 Buscando en documentos...' : '🔍 Consultar Base de Conocimientos'}
        </button>

        {answer && (
          <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-5 mb-4">
            <p className="text-xs text-gray-500 mb-2">💡 Respuesta:</p>
            <p className="text-sm text-gray-200 whitespace-pre-wrap">{answer}</p>
            <button onClick={()=>navigator.clipboard.writeText(answer)} className="mt-3 px-4 py-2 bg-white/10 rounded-lg text-xs hover:bg-white/20 transition text-white">📋 Copiar</button>
          </div>
        )}

        {sources.length > 0 && (
          <div className="bg-white/[0.02] border border-white/5 rounded-xl p-4">
            <p className="text-xs text-gray-500 mb-3">📎 Fuentes encontradas ({sources.length}):</p>
            <div className="space-y-2">
              {sources.map((s, i) => (
                <div key={i} className="flex gap-2 items-start">
                  <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-bold flex-shrink-0 ${s.relevance==='high'?'bg-emerald-500/20 text-emerald-400':s.relevance==='medium'?'bg-amber-500/20 text-amber-400':'bg-gray-500/20 text-gray-400'}`}>
                    {s.relevance==='high'?'★★★':s.relevance==='medium'?'★★':'★'}
                  </span>
                  <div className="min-w-0">
                    <p className="text-[10px] text-gray-500">{s.source} · fragmento {s.chunk}</p>
                    <p className="text-xs text-gray-400 truncate">{s.preview}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ── MAIN ── */
export default function App() {
  const [active, setActive] = useState('home');
  const [collapsed, setCollapsed] = useState(false);

  const navigate = (catId: string, toolId?: string) => {
    if (toolId) setActive(toolId);
    else setActive(catId);
  };

  const goBack = () => {
    const tool = TOOLS.find(t=>t.id===active);
    if (tool) setActive(tool.category);
    else setActive('home');
  };

  const renderContent = () => {
    if (active === 'home') return <HomePage onSelect={navigate}/>;
    const tool = TOOLS.find(t=>t.id===active);
    if (tool) return <ToolPage toolId={active} onBack={goBack}/>;
    const cat = CATEGORIES.find(c=>c.id===active);
    if (cat) return <CategoryPage catId={active} onSelect={navigate}/>;
    return <HomePage onSelect={navigate}/>;
  };

  return (
    <div className="flex h-screen bg-[#0f0f1a] text-white overflow-hidden">
      <Sidebar active={active} onSelect={navigate} collapsed={collapsed} onToggle={()=>setCollapsed(!collapsed)}/>
      <main className="flex-1 overflow-y-auto">
        {renderContent()}
      </main>
    </div>
  );
}