/**
 * AI Hub Studio - API Client
 * Connects to the Gateway at http://100.105.27.27:9000/v1
 */

const GATEWAY_URL = process.env.NEXT_PUBLIC_GATEWAY_URL || 'http://100.105.27.27:9000/v1';

export interface ServiceStatus {
  status: string;
  models?: string[];
}

export interface HubStatus {
  status: string;
  services: Record<string, ServiceStatus>;
  gpu: {
    available: boolean;
    name?: string;
    vram_total_mb?: number;
    vram_used_mb?: number;
    vram_free_mb?: number;
    temperature_c?: number;
    utilization_pct?: number;
  };
}

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface ChatResponse {
  id: string;
  choices: Array<{
    message: ChatMessage;
    finish_reason: string;
  }>;
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

// Generate image
export async function generateImage(params: {
  prompt: string;
  model?: string;
  negative_prompt?: string;
  width?: number;
  height?: number;
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

// === TTS (Text-to-Speech) ===
export async function generateSpeech(params: {
  input: string;
  model?: string; // 'piper' | 'xtts' | 'fish'
  voice?: string;
  language?: string;
  speaker_wav?: string;
  response_format?: string;
}): Promise<Blob> {
  const res = await fetch(`${GATEWAY_URL}/audio/speech`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(`TTS error: ${res.status}`);
  return res.blob();
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
  model?: string; // 'musetalk' | 'latentsync' | 'sadtalker' | 'wav2lip'
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
  model?: string; // 'liveportrait'
}): Promise<{ video_url: string; model: string }> {
  const res = await fetch(`${GATEWAY_URL}/avatar/portrait`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(`Portrait animation error: ${res.status}`);
  return res.json();
}

// === Digital Human (Full Pipeline: LLM → TTS → Lip-sync) ===
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
// Backend expects multipart/form-data with 'file' or 'image_url'
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
  return res.blob(); // Returns image binary
}

// === Effects: Upscale ===
// Backend expects multipart/form-data with 'file' or 'image_url'
export async function upscaleImage(params: {
  file?: File;
  image_url?: string;
  scale?: number; // 2, 4
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
  return res.blob(); // Returns image binary
}
