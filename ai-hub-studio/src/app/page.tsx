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
  { id: 'video-gen', name: 'Wan2GP', icon: '🎬', desc: 'WAN 2.1 - Genera videos tipo Sora desde texto. 480p/720p, 3-10s', gradient: 'from-blue-600 to-cyan-500', status: 'online', category: 'video', equivalent: 'Sora AI / Kling', url: `${GRADIO}:7860` },
  { id: 'cogvideox', name: 'CogVideoX (THUDM)', icon: '🎥', desc: 'Video generation de alta calidad. El mejor modelo open-source', gradient: 'from-blue-700 to-indigo-500', status: 'planned', category: 'video', equivalent: 'Pika AI', url: `${GRADIO}:7861` },
  { id: 'open-sora', name: 'Open-Sora (HPC-AI Tech)', icon: '🎞️', desc: 'Video generation tipo Sora 100% open source', gradient: 'from-indigo-600 to-violet-500', status: 'planned', category: 'video', equivalent: 'Sora AI' },
  { id: 'hunyuan', name: 'HunyuanVideo (Tencent)', icon: '📹', desc: 'Video fotorrealista de alta calidad', gradient: 'from-sky-600 to-blue-500', status: 'online', category: 'video', equivalent: 'Kling AI', url: `${GRADIO}:8188` },
  { id: 'story-diffusion', name: 'StoryDiffusion', icon: '📖', desc: 'Personajes consistentes -> comic -> video. Ideal para series', gradient: 'from-indigo-500 to-purple-500', status: 'planned', category: 'video', equivalent: 'Series YouTube' },
  { id: 'avatar-gen', name: 'Hallo2 (Fudan)', icon: '🎭', desc: 'Sube foto + audio -> video del avatar hablando', gradient: 'from-amber-500 to-orange-500', status: 'online', category: 'avatar', equivalent: 'HeyGen', url: `${GRADIO}:8070` },
  { id: 'lipsync', name: 'LatentSync (ByteDance)', icon: '👄', desc: 'Sincronizacion labios perfecta con difusion', gradient: 'from-cyan-500 to-blue-500', status: 'online', category: 'avatar', equivalent: 'HeyGen Lip-sync', url: `${GRADIO}:8043` },
  { id: 'live-portrait', name: 'LivePortrait (KwaiVGI)', icon: '🖼️', desc: 'Anima fotos con expresiones faciales naturales', gradient: 'from-pink-500 to-rose-500', status: 'online', category: 'avatar', equivalent: 'HeyGen Express', url: `${GRADIO}:8044` },
  { id: 'musetalk', name: 'MuseTalk (TME)', icon: '🗣️', desc: 'Lip-sync en tiempo real - Pipeline de avatar hablando', gradient: 'from-teal-500 to-emerald-500', status: 'online', category: 'avatar', equivalent: 'HeyGen Live', url: `${GRADIO}:8040` },
  { id: 'digital-human', name: 'Humano Digital', icon: '🧑‍💻', desc: 'Pipeline completo: LLM + TTS + Lip-sync + Animacion', gradient: 'from-emerald-500 to-teal-500', status: 'planned', category: 'avatar', equivalent: 'HeyGen Pro' },
  { id: 'ai-vtuber', name: 'AI VTuber', icon: '🎮', desc: 'VTuber con IA: TTS + Live2D + Stream automatico', gradient: 'from-violet-500 to-fuchsia-500', status: 'planned', category: 'avatar', equivalent: 'VTuber Studio' },
  { id: 'music-gen', name: 'DocuMusic', icon: '🎵', desc: 'ACE-Step, YuE, DiffRhythm - Canciones completas tipo Suno', gradient: 'from-green-500 to-emerald-500', status: 'online', category: 'music', equivalent: 'Suno.AI', url: `${GRADIO}:8000` },
  { id: 'image-gen', name: 'ComfyUI', icon: '🎨', desc: 'SDXL, Flux - Imagenes fotorrealistas, arte, logos, banners', gradient: 'from-purple-500 to-pink-500', status: 'online', category: 'image', equivalent: 'Midjourney / Freepik', url: `${GRADIO}:8188` },
  { id: 'marketing-copy', name: 'Copy Publicitario (Llama 3.1)', icon: '📝', desc: 'Anuncios, emails, slogans - Textos persuasivos con IA', gradient: 'from-orange-500 to-red-500', status: 'online', category: 'marketing', equivalent: 'Jasper AI' },
  { id: 'social-post', name: 'Post Redes (Llama 3.1)', icon: '📱', desc: 'Contenido viral para Instagram, TikTok, YouTube, X', gradient: 'from-rose-500 to-pink-500', status: 'online', category: 'marketing', equivalent: 'Buffer AI' },
  { id: 'blog-writer', name: 'Blog Writer (Llama 3.1)', icon: '✍️', desc: 'Articulos SEO completos con keywords y estructura', gradient: 'from-amber-500 to-yellow-500', status: 'online', category: 'marketing', equivalent: 'Copy.ai' },
  { id: 'slogan-gen', name: 'Slogan Generator (Llama 3.1)', icon: '💡', desc: 'Frases pegadizas para tu marca o campana', gradient: 'from-yellow-500 to-amber-500', status: 'online', category: 'marketing', equivalent: 'Branding AI' },
  { id: 'video-effects', name: 'Higgsfield AI', icon: '⚡', desc: 'Motion control, camara, efectos tipo Higgsfield', gradient: 'from-red-500 to-orange-500', status: 'online', category: 'effects', equivalent: 'Higgsfield AI', url: `${GRADIO}:8052` },
  { id: 'image-upscale', name: 'Real-ESRGAN', icon: '🔍', desc: 'Mejora resolucion hasta 4x con upscaling inteligente', gradient: 'from-slate-500 to-gray-500', status: 'online', category: 'effects', equivalent: 'Upscale.media', url: `${GRADIO}:8051` },
  { id: 'bg-remove', name: 'Rembg', icon: '✂️', desc: 'Elimina fondos automaticamente con IA', gradient: 'from-gray-500 to-zinc-500', status: 'online', category: 'effects', equivalent: 'Remove.bg', url: `${GRADIO}:8050` },
  { id: 'tts', name: 'Piper TTS', icon: '🎙️', desc: 'Text-to-Speech en español. Rapido en CPU', gradient: 'from-teal-500 to-emerald-500', status: 'online', category: 'chat', equivalent: 'ElevenLabs', url: `${GRADIO}:8010` },
  { id: 'xtts', name: 'XTTS-v2', icon: '🗣️', desc: 'TTS multilingue con clonacion de voz. Sube un audio y clona cualquier voz', gradient: 'from-orange-500 to-red-500', status: 'planned', category: 'chat', equivalent: 'ElevenLabs Voice Cloning', url: `${GRADIO}:8011` },
  { id: 'fish', name: 'Fish Speech', icon: '🐟', desc: 'TTS alternativo con voces naturales. Soporte multilingue', gradient: 'from-blue-500 to-cyan-500', status: 'planned', category: 'chat', equivalent: 'PlayHT', url: `${GRADIO}:8012` },
  { id: 'stt', name: 'Whisper large-v3', icon: '🎤', desc: 'Speech-to-Text OpenAI. Transcribe audio en 100+ idiomas', gradient: 'from-sky-500 to-indigo-500', status: 'online', category: 'chat', equivalent: 'Whisper API', url: `${GRADIO}:8020` },
  { id: 'chat-ai', name: 'AI Chat (Qwen 2.5 + Llama 3.1)', icon: '🤖', desc: 'Asistente local sin limites, zero tokens. Qwen 2.5 (mejor en español) o Llama 3.1', gradient: 'from-violet-500 to-purple-500', status: 'online', category: 'chat', equivalent: 'ChatGPT' },
];

// LLM models available in Ollama (IDs must match Ollama tags exactly)
const LLM_MODELS = [
  { id: 'qwen2.5:7b', name: 'Qwen 2.5 7B', desc: 'Mejor razonamiento y español', icon: '🧠' },
  { id: 'qwen2.5-coder:7b', name: 'Qwen 2.5 Coder', desc: 'Especializado en programación', icon: '💻' },
  { id: 'llama3.1', name: 'Llama 3.1', desc: 'Rápido y versátil', icon: '🦙' },
];

import { chatCompletions, chatCompletionsStream, getHubStatus } from '../lib/api';

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
          <span className={`text-[10px] px-2 py-1 rounded-full font-bold ${gpu?.available ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
            {gpu?.available ? '● ONLINE' : '● OFFLINE'}
          </span>
        </div>
        {gpu?.available ? (
          <div className="space-y-3">
            <GpuMetricBar
              label="VRAM"
              used={Math.round((gpu.vram_used_mb || 0) / 1024)}
              total={Math.round((gpu.vram_total_mb || 16384) / 1024)}
              unit="GB"
              color="bg-gradient-to-r from-emerald-500 to-teal-400"
            />
            {gpu.temperature_c !== undefined && (
              <div className="flex items-center justify-between">
                <span className="text-[11px] text-gray-500">🌡️ Temperatura</span>
                <span className={`text-xs font-mono font-bold ${gpu.temperature_c > 80 ? 'text-red-400' : gpu.temperature_c > 65 ? 'text-amber-400' : 'text-emerald-400'}`}>
                  {gpu.temperature_c}°C
                </span>
              </div>
            )}
            {gpu.utilization_pct !== undefined && (
              <GpuMetricBar
                label="⚡ Uso GPU"
                used={gpu.utilization_pct}
                total={100}
                unit="%"
                color="bg-gradient-to-r from-blue-500 to-cyan-400"
              />
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

      {/* Services List */}
      {servicesArray.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-bold text-white mb-4">Servicios del Hub</h2>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
            {servicesArray.map((s:any) => (
              <div key={s.name} className="flex items-center gap-2 bg-white/[0.02] border border-white/5 rounded-lg px-3 py-2">
                <StatusDot status={s.status}/>
                <span className="text-xs text-gray-300 capitalize truncate">{s.name}</span>
              </div>
            ))}
          </div>
        </div>
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
    case 'marketing-copy': case 'social-post': case 'blog-writer': case 'slogan-gen': return <MarketingTool tool={tool}/>;
    case 'chat-ai': return <ChatTool/>;
    default: return <div className="flex items-center justify-center h-full text-gray-500">Interfaz disponible cuando el servicio este activo.</div>;
  }
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