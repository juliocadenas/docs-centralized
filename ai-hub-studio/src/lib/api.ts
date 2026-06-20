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