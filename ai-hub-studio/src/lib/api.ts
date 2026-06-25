x/**
 * AI Hub Studio - API Client
 * Connects to the Gateway at http://100.105.27.27:9000/v1
 */

const GATEWAY_URL = process.env.NEXT_PUBLIC_GATEWAY_URL || 'http://100.105.27.27:9000/v1';

export interface ServiceStatus {
  name: string;
  display_name: string;
  status: 'online' | 'offline' | 'unknown' | 'error';
  url: string;
  port: number;
  type: string;
  categories: string[];
  vram_mb: number;
  always_on: boolean;
  idle_seconds?: number;
  response_time_ms?: number;
  error?: string;
}

export interface HubStatus {
  status: 'ok' | 'degraded';
  gateway_version: string;
  uptime_seconds: number;
  services: ServiceStatus[];
  services_summary: {
    total: number;
    online: number;
    offline: number;
    always_on_total: number;
    always_on_online: number;
    always_on_offline: string[];
  };
  gpu: {
    gpu_name?: string;
    total_vram_mb: number;
    used_vram_mb?: number;
    free_vram_mb?: number;
    gpu_utilization?: number;
    temperature?: number;
    error?: string;
  };
  gpu_queue_waiting: number;
}

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
  name?: string;
}

export interface ChatResponse {
  id: string;
  choices: Array<{
    message: ChatMessage;
    finish_reason: string;
  }>;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export interface ImageGenResponse {
  data: Array<{
    url?: string;
    b64_json?: string;
  }>;
}

export interface ModelInfo {
  id: string;
  object: string;
  owned_by: string;
  type?: string;
  service?: string;
  vram_mb?: number;
  status?: string;
}

// Fetch hub status
export async function getHubStatus(): Promise<HubStatus> {
  const res = await fetch(`${GATEWAY_URL}/status`);
  if (!res.ok) throw new Error('Gateway unavailable');
  return res.json();
}

// List models
export async function listModels(): Promise<{ data: ModelInfo[] }> {
  const res = await fetch(`${GATEWAY_URL}/models`);
  if (!res.ok) throw new Error('Cannot fetch models');
  return res.json();
}

// Chat with LLM
export async function chatCompletions(
  messages: ChatMessage[],
  model = 'qwen2.5:7b',
  options?: { temperature?: number; max_tokens?: number }
): Promise<ChatResponse> {
  const res = await fetch(`${GATEWAY_URL}/chat/completions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model,
      messages,
      temperature: options?.temperature ?? 0.7,
      max_tokens: options?.max_tokens ?? 4096,
    }),
  });
  if (!res.ok) throw new Error(`Chat error: ${res.status}`);
  return res.json();
}

/**
 * Stream chat completion tokens from the Gateway (SSE).
 * Calls onToken for each token chunk received.
 * Returns the full accumulated text when done.
 */
export async function chatCompletionsStream(
  messages: ChatMessage[],
  onToken: (token: string, fullText: string) => void,
  model = 'qwen2.5:7b',
  options?: { temperature?: number; max_tokens?: number }
): Promise<string> {
  const res = await fetch(`${GATEWAY_URL}/chat/completions/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model,
      messages,
      stream: true,
      temperature: options?.temperature ?? 0.7,
      max_tokens: options?.max_tokens ?? 4096,
    }),
  });

  if (!res.ok) throw new Error(`Chat stream error: ${res.status}`);
  if (!res.body) throw new Error('No response body for streaming');

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let fullText = '';
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue;
      const dataStr = line.slice(6).trim();
      if (dataStr === '[DONE]') continue;

      try {
        const chunk = JSON.parse(dataStr);
        if (chunk.error) {
          throw new Error(chunk.error);
        }
        const delta = chunk.choices?.[0]?.delta?.content;
        if (delta) {
          fullText += delta;
          onToken(delta, fullText);
        }
      } catch (e) {
        if (e instanceof Error && !e.message.includes('JSON')) {
          throw e;
        }
      }
    }
  }

  return fullText;
}

// Generate image - with advanced ComfyUI parameters
export async function generateImage(params: {
  prompt: string;
  model?: string;        // 'flux' | 'sdxl' | 'sd15'
  negative_prompt?: string;
  width?: number;        // default 1024
  height?: number;       // default 1024
  steps?: number;        // 15-50 (default 20)
  cfg?: number;          // 1-20 (default 7.0)
  sampler_name?: string; // 'euler', 'dpmpp_2m', 'ddim'
  scheduler?: string;    // 'normal', 'karras', 'exponential'
  seed?: number;         // -1 = random
  batch_size?: number;   // generate multiple
}): Promise<ImageGenResponse> {
  const res = await fetch(`${GATEWAY_URL}/images/generations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(`Image gen error: ${res.status}`);
  return res.json();
}

// Generate video
export async function generateVideo(params: {
  prompt: string;
  model?: string;
  duration_seconds?: number;
  resolution?: string;
}) {
  const res = await fetch(`${GATEWAY_URL}/video/generations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(`Video gen error: ${res.status}`);
  return res.json();
}

// Generate audio/music
export async function generateAudio(params: {
  prompt: string;
  model?: string;
  duration_seconds?: number;
}) {
  const res = await fetch(`${GATEWAY_URL}/audio/generations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(`Audio gen error: ${res.status}`);
  return res.json();
}

// Marketing-specific helpers using LLM
export async function generateMarketingCopy(params: {
  type: 'ad' | 'social' | 'email' | 'slogan' | 'blog';
  product: string;
  audience: string;
  tone: string;
  language?: string;
}): Promise<string> {
  const systemPrompt = `Eres un experto en marketing digital y copywriting. Generas contenido publicitario persuasivo y creativo. 
Idioma: ${params.language || 'español'}.
Formato: responde SOLO con el contenido solicitado, sin explicaciones adicionales.`;

  const userPrompt = `Genera ${params.type === 'ad' ? 'un anuncio publicitario' : params.type === 'social' ? 'un post para redes sociales' : params.type === 'email' ? 'un email marketing' : params.type === 'slogan' ? '5 slogans creativos' : 'un artículo de blog'} para:
Producto/Servicio: ${params.product}
Público objetivo: ${params.audience}
Tono: ${params.tone}`;

  const response = await chatCompletions([
    { role: 'system', content: systemPrompt },
    { role: 'user', content: userPrompt },
  ]);
  return response.choices[0].message.content;
}

// Start/stop services
export async function manageService(service: string, action: 'start' | 'stop') {
  const res = await fetch(`${GATEWAY_URL}/services/${service}/${action}`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error(`Service ${action} error`);
  return res.json();
}

// === TTS (Text-to-Speech) with Fallback Chain ===
export interface TTSResult {
  blob: Blob;
  engineUsed: string;
  fellBack: boolean;
}

const TTS_FALLBACK_CHAIN: Record<string, string[]> = {
  piper: ['piper', 'xtts', 'fish'],
  xtts: ['xtts', 'piper', 'fish'],
  fish: ['fish', 'piper', 'xtts'],
};

export async function generateSpeech(params: {
  input: string;
  model?: string;
  voice?: string;
  language?: string;
  speaker_wav?: string;
  response_format?: string;
}): Promise<Blob> {
  const result = await generateSpeechWithFallback(params);
  return result.blob;
}

export async function generateSpeechWithFallback(params: {
  input: string;
  model?: string;
  voice?: string;
  language?: string;
  speaker_wav?: string;
  response_format?: string;
}): Promise<TTSResult> {
  const requestedEngine = params.model || 'piper';
  const chain = TTS_FALLBACK_CHAIN[requestedEngine] || TTS_FALLBACK_CHAIN.piper;
  let lastError = '';

  for (const engine of chain) {
    try {
      const res = await fetch(`${GATEWAY_URL}/audio/speech`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...params, model: engine }),
      });
      if (res.ok) {
        return {
          blob: await res.blob(),
          engineUsed: engine,
          fellBack: engine !== requestedEngine,
        };
      }
      lastError = `TTS ${engine}: HTTP ${res.status}`;
    } catch (e: any) {
      lastError = e.message || `TTS ${engine} failed`;
    }
  }
  throw new Error(`Todos los motores TTS fallaron. Ultimo error: ${lastError}`);
}

// === STT (Speech-to-Text) ===
export async function transcribeAudio(params: {
  file: File;
  language?: string;
  model?: string;
}): Promise<{ text: string; language?: string; duration?: number }> {
  const formData = new FormData();
  formData.append('file', params.file);
  formData.append('language', params.language || 'es');
  if (params.model) formData.append('model', params.model);

  const res = await fetch(`${GATEWAY_URL}/audio/transcriptions`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error(`STT error: ${res.status}`);
  return res.json();
}

// === List available TTS voices ===
export async function listVoices(): Promise<{
  engines: string[];
  voices: Record<string, string[]>;
}> {
  const res = await fetch(`${GATEWAY_URL}/audio/voices`);
  if (!res.ok) throw new Error('Cannot fetch voices');
  return res.json();
}

// === Avatar / Lip-sync ===
export async function lipsyncVideo(params: {
  video_url?: string;
  audio_url?: string;
  model?: string;
}): Promise<{ video_url: string; model: string }> {
  const res = await fetch(`${GATEWAY_URL}/avatar/lipsync`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(`Lipsync error: ${res.status}`);
  return res.json();
}

// === Avatar / Portrait Animation ===
export async function animatePortrait(params: {
  source_image_url: string;
  driving_video_url: string;
  relative_motion?: boolean;
  model?: string;
}): Promise<{ video_url: string; model: string }> {
  const res = await fetch(`${GATEWAY_URL}/avatar/portrait`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(`Portrait animation error: ${res.status}`);
  return res.json();
}

// === Digital Human (Full Pipeline: LLM -> TTS -> Lip-sync) ===
export async function createDigitalHuman(params: {
  prompt: string;
  image_url?: string;
  llm_model?: string;
  tts_model?: string;
  lipsync_model?: string;
  voice?: string;
  language?: string;
}): Promise<{
  text: string;
  audio_url: string;
  video_url: string;
}> {
  const res = await fetch(`${GATEWAY_URL}/avatar/digital-human`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(`Digital human error: ${res.status}`);
  return res.json();
}

// === Effects: Remove Background ===
export async function removeBackground(params: {
  file?: File;
  image_url?: string;
  return_mask?: boolean;
}): Promise<Blob> {
  const formData = new FormData();
  if (params.file) {
    formData.append('file', params.file);
  } else if (params.image_url) {
    formData.append('image_url', params.image_url);
  } else {
    throw new Error('Provide file or image_url');
  }
  if (params.return_mask) {
    formData.append('return_mask', 'true');
  }

  const res = await fetch(`${GATEWAY_URL}/effects/remove-bg`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error(`Remove bg error: ${res.status}`);
  return res.blob();
}

// === Effects: Upscale ===
export async function upscaleImage(params: {
  file?: File;
  image_url?: string;
  scale?: number;
}): Promise<Blob> {
  const formData = new FormData();
  if (params.file) {
    formData.append('file', params.file);
  } else if (params.image_url) {
    formData.append('image_url', params.image_url);
  } else {
    throw new Error('Provide file or image_url');
  }
  if (params.scale) {
    formData.append('scale', params.scale.toString());
  }

  const res = await fetch(`${GATEWAY_URL}/effects/upscale`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error(`Upscale error: ${res.status}`);
  return res.blob();
}

// === Embeddings (text vectors) ===
export async function createEmbeddings(
  input: string,
  model = 'nomic-embed-text'
): Promise<{ data: Array<{ embedding: number[] }> }> {
  const res = await fetch(`${GATEWAY_URL}/embeddings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model, input }),
  });
  if (!res.ok) throw new Error(`Embeddings error: ${res.status}`);
  return res.json();
}

// === Vision (image analysis) ===
export async function analyzeImage(params: {
  image_url: string;
  prompt?: string;
  model?: string;
}): Promise<ChatResponse> {
  const res = await fetch(`${GATEWAY_URL}/chat/vision`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      image_url: params.image_url,
      prompt: params.prompt || 'Describe esta imagen en detalle.',
      model: params.model || 'qwen2.5vl:7b',
    }),
  });
  if (!res.ok) throw new Error(`Vision error: ${res.status}`);
  return res.json();
}

// === Warm model (pre-load into VRAM) ===
export async function warmModel(model: string): Promise<{ status: string; model: string }> {
  const res = await fetch(`${GATEWAY_URL}/models/warm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model }),
  });
  if (!res.ok) throw new Error(`Warm model error: ${res.status}`);
  return res.json();
}

// === Fast health check ===
export async function healthCheck(): Promise<{
  status: string;
  version: string;
  uptime_seconds: number;
}> {
  const res = await fetch(`${GATEWAY_URL}/health`);
  if (!res.ok) throw new Error('Gateway not responding');
  return res.json();
}

// === Agentic Video Pipeline (OpenMontage + Remotion) ===
export interface AgenticVideoResponse {
  job_id: string;
  status: string;
  message: string;
  estimated_time_seconds: number;
}

export interface AgenticVideoStatus {
  job_id: string;
  status: 'started' | 'processing' | 'completed' | 'error';
  progress: number;
  message: string;
  video_url?: string;
  video_path?: string;
  timestamp?: number;
}

export async function createAgenticVideo(params: {
  topic: string;
  duration_seconds?: number;
  style?: string;
  language?: string;
  voice?: string;
  model?: string;
}): Promise<AgenticVideoResponse> {
  const res = await fetch(`${GATEWAY_URL}/video/agentic`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(`Agentic video error: ${res.status}`);
  return res.json();
}

export async function getAgenticVideoStatus(jobId: string): Promise<AgenticVideoStatus> {
  const res = await fetch(`${GATEWAY_URL}/video/agentic/${jobId}/status`);
  if (!res.ok) throw new Error(`Status check error: ${res.status}`);
  return res.json();
}

// === Infrastructure info ===
export async function getInfrastructure(): Promise<{
  gateway: Record<string, unknown>;
  server: Record<string, unknown>;
  services: ServiceStatus[];
  gpu: Record<string, unknown>;
  storage: Record<string, unknown>;
  network: Record<string, unknown>;
  models_count: number;
}> {
  const res = await fetch(`${GATEWAY_URL}/infrastructure`);
  if (!res.ok) throw new Error('Cannot fetch infrastructure info');
  return res.json();
}