/**
 * src/core/lib/pricing.ts
 * -----------------------
 * Centralized pricing calculations for Oorumart & YesFancy.
 * Single source of truth for converting MRP and Discount % into effective selling prices.
 */

/**
 * Calculates the effective customer selling price rounded to the nearest rupee.
 * Formula: round(mrp * (1 - discount / 100))
 * 
 * Examples:
 * - getSellingPrice(1000, 20) -> 800
 * - getSellingPrice(499, 15)  -> 424
 * - getSellingPrice(500, 0)   -> 500
 */
export function getSellingPrice(mrp: number | string, discount: number | string = 0): number {
  const m = Number(mrp) || 0;
  const d = Number(discount) || 0;
  if (m <= 0) return 0;
  if (d <= 0) return Math.round(m);
  return Math.round(m * (1 - d / 100));
}

/**
 * Calculates customer savings amount for a given quantity.
 * Formula: max(0, (mrp - selling_price) * qty)
 */
export function getSavingsAmount(mrp: number | string, discount: number | string = 0, qty: number = 1): number {
  const m = Number(mrp) || 0;
  const price = getSellingPrice(m, discount);
  const q = Number(qty) || 1;
  return Math.max(0, (m - price) * q);
}
