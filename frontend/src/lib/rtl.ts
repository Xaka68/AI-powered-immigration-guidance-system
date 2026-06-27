const RTL_LANGS = new Set(["ar", "fa", "ckb", "ur", "he"]);

export function isRTL(lang: string | null | undefined): boolean {
  if (!lang) return false;
  const base = lang.toLowerCase().split(/[-_]/)[0];
  return RTL_LANGS.has(base);
}
