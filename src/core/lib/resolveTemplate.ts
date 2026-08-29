/**
 * src/lib/resolveTemplate.ts
 * 
 * Dynamic Lazy-Loading Template Resolver:
 * - Pre-bundles all templates in /src/templates/*.astro into split lazy chunks via Vite import.meta.glob.
 * - Dynamically loads ONLY the 1 requested template into RAM per request (0 RAM bloat).
 * - Guaranteed fallback to GiftShopTemplate1 if requested template ID is missing/invalid.
 */

// Vite static analysis scans /src/templates/*.astro into separate lazy chunks
const templates = import.meta.glob('../templates/*.astro');

export async function getTemplateComponent(templateId: string) {
  // Normalize template key mapping
  let normalizedId = templateId || 'GiftShopTemplate1';
  
  if (normalizedId === 'gift_novelty_template_1' || normalizedId === 'gift_novelty_template_2' || normalizedId === 'gift_shop_template_1' || normalizedId === 'gift_novelty') {
    normalizedId = 'GiftShopTemplate1';
  } else if (normalizedId === 'minimal' || normalizedId === 'minimal_grid' || normalizedId === 'fmcg') {
    normalizedId = 'MinimalGridTemplate';
  }

  const targetPath = `../templates/${normalizedId}.astro`;

  try {
    if (templates[targetPath]) {
      const module: any = await templates[targetPath]();
      return module.default;
    }
  } catch (err) {
    console.warn(`[TemplateResolver] Error loading template '${templateId}', using fallback.`, err);
  }

  // Fallback to GiftShopTemplate1
  const fallbackModule: any = await templates['../templates/GiftShopTemplate1.astro']();
  return fallbackModule.default;
}
