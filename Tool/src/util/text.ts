import crypto from 'node:crypto';

export function computeContentHash(text: string): string {
  return crypto.createHash('sha256').update(text, 'utf8').digest('hex');
}

export function redactSecrets(text: string): string {
  let redacted = text;
  // Simple token patterns
  redacted = redacted.replace(/(sk-[A-Za-z0-9]{20,})/g, '[REDACTED_SECRET]');
  redacted = redacted.replace(/(ghp_[A-Za-z0-9]{20,})/g, '[REDACTED_SECRET]');
  redacted = redacted.replace(/(eyJ[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,})/g, '[REDACTED_JWT]');
  redacted = redacted.replace(/([\w.-]+@[\w.-]+\.[A-Za-z]{2,})/g, '[REDACTED_EMAIL]');
  redacted = redacted.replace(/(\b\d{1,3}(?:\.\d{1,3}){3}\b)/g, '[REDACTED_IP]');
  return redacted;
}

