import { z } from 'zod';

export const ShopConfigSchema = z.object({
  shop: z.object({
    slug: z.string().min(2).max(63),
    name: z.string().min(2),
    category: z.enum(['gift_novelty', 'boutique', 'nail_accessories', 'florist', 'paan_beverage']),
    template: z.string(),
    phone: z.string(),
    announcement_text: z.string().optional(),
    
    theme: z.object({
      primary_color: z.string().regex(/^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/),
      secondary_color: z.string().regex(/^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/),
      background_color: z.string().regex(/^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/),
      font_family: z.string().default('Outfit'),
    }),

    carousels: z.object({
      offer_banners: z.array(z.object({
        title: z.string(),
        subtitle: z.string().optional(),
        image: z.string().url(),
        category_id: z.string().optional(),
      })).default([]),
      product_gallery: z.array(z.string().url()).default([]),
    }).optional(),

    delivery_options: z.object({
      store_pickup: z.object({
        enabled: z.boolean().default(true),
        time_slots: z.array(z.string()).optional(),
      }).optional(),
      home_delivery: z.object({
        enabled: z.boolean().default(true),
        delivery_fee: z.number().default(0),
        min_order_amount: z.number().default(0),
        max_radius_km: z.number().optional(),
      }).optional(),
      subscription: z.object({
        enabled: z.boolean().default(false),
        frequencies: z.array(z.string()).optional(),
      }).optional(),
    }),

    categories: z.array(z.object({
      id: z.string(),
      label: z.string(),
      icon_url: z.string().optional(),
    })),

    products: z.array(z.object({
      id: z.string(),
      name: z.string(),
      category_id: z.string(),
      price: z.number(),
      mrp: z.number().optional(),
      badge: z.string().optional(),
      image_url: z.string().url(),
      is_available: z.boolean().default(true),
    })),
  }),
});

export type ShopConfig = z.infer<typeof ShopConfigSchema>;
