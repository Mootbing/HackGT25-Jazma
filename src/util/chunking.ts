export function chunkText(text: string, options?: { chunkSize?: number; overlap?: number }): string[] {
  const chunkSize = options?.chunkSize ?? 800;
  const overlap = options?.overlap ?? 100;
  const cleaned = text.replace(/\s+/g, ' ').trim();
  if (cleaned.length === 0) return [];
  const chunks: string[] = [];
  let start = 0;
  while (start < cleaned.length) {
    const end = Math.min(cleaned.length, start + chunkSize);
    chunks.push(cleaned.slice(start, end));
    if (end === cleaned.length) break;
    start = Math.max(0, end - overlap);
  }
  return chunks;
}

