import OpenAI from 'openai';

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

const embeddingModel = process.env.EMBEDDING_MODEL || 'text-embedding-3-small';
const embeddingDim = Number(process.env.EMBEDDING_DIM || '1536');

export async function textEmbedding(text: string): Promise<number[]> {
  const input = text.length > 8000 ? text.slice(0, 8000) : text;
  const res = await openai.embeddings.create({
    model: embeddingModel,
    input
  });
  const vec = res.data[0].embedding;
  return normalizeVector(vec);
}

export async function embedChunks(chunks: string[]): Promise<number[][]> {
  if (chunks.length === 0) return [];
  const inputs = chunks.map((c) => (c.length > 8000 ? c.slice(0, 8000) : c));
  const res = await openai.embeddings.create({
    model: embeddingModel,
    input: inputs
  });
  const vectors = res.data.map(d => normalizeVector(d.embedding));
  return vectors;
}

function normalizeVector(vec: number[]): number[] {
  // Enforce expected dimension if provider changes
  const v = vec.slice(0, embeddingDim);
  const norm = Math.sqrt(v.reduce((acc, x) => acc + x * x, 0));
  return v.map(x => x / (norm || 1));
}

