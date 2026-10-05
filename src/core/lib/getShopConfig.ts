import { createClient } from '@supabase/supabase-js';

function getSupabaseClient() {
  const url = (typeof import.meta !== 'undefined' && import.meta.env ? import.meta.env.PUBLIC_SUPABASE_URL : null) 
    || (typeof process !== 'undefined' && process.env ? process.env.PUBLIC_SUPABASE_URL : null)
    || 'https://fwrievuhudjkeffmszqf.supabase.co';
    
  const key = (typeof import.meta !== 'undefined' && import.meta.env ? (import.meta.env.SUPABASE_SERVICE_ROLE_KEY || import.meta.env.PUBLIC_SUPABASE_ANON_KEY) : null) 
    || (typeof process !== 'undefined' && process.env ? (process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.PUBLIC_SUPABASE_ANON_KEY) : null)
    || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ3cmlldnVodWRqa2VmZm1zenFmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ0Mjc1MDQsImV4cCI6MjA5MDAwMzUwNH0.NrucFfwz8vsgF8kMp2aHMK_PW-4Sf-J7cCv3dpRPw0U';

  if (url && key) {
    return createClient(url, key);
  }
  return null;
}

const tagLabelMap: Record<string, string> = {
  all: 'All Products',
  novelties: 'Gift Store',
  decor: 'Home & Decor',
  games: 'Games',
  toys: 'Toys',
  lunchbox: 'Lunch Boxes',
  fashion: 'Beauty & Lifestyle'
};

function formatTagLabel(tag: string): string {
  if (tagLabelMap[tag]) return tagLabelMap[tag];
  return tag
    .replace(/_/g, ' ')
    .replace(/-/g, ' ')
    .replace(/\b\w/g, char => char.toUpperCase());
}

const defaultOfferSlides = [
  {
    id: "slide_beauty_lifestyle",
    title: "BEAUTY & LIFESTYLE",
    subtitle: "Curated luxury fragrances, fine jewellery & premium personal care.",
    image_url: "/images/offer_beauty_lifestyle.webp",
    tag_id: "fashion",
    link: "/catalog?shop=yesfancy&category=fashion"
  },
  {
    id: "slide_gift_store",
    title: "FESTIVE GIFT STORE",
    subtitle: "Curated luxury hampers, fancy boxes & novelties for every occasion.",
    image_url: "/images/offer_gift_store.webp",
    tag_id: "novelties",
    link: "/catalog?shop=yesfancy&category=novelties"
  },
  {
    id: "slide_home_decor",
    title: "MODERN HOME & DECOR",
    subtitle: "Fancy minimal interiors, designer lamps & contemporary living accents.",
    image_url: "/images/offer_home_decor.webp",
    tag_id: "decor",
    link: "/catalog?shop=yesfancy&category=decor"
  },
  {
    id: "slide_games",
    title: "GAMES & PUZZLES",
    subtitle: "Interactive arcade labyrinths, marble runs & brain exercising games.",
    image_url: "/images/offer_games.webp",
    tag_id: "games",
    link: "/catalog?shop=yesfancy&category=games"
  },
  {
    id: "slide_toys",
    title: "ACTION TOYS & ROBOTICS",
    subtitle: "Functional hydraulic crane kits, robotic arms & mechanical dynamic machines.",
    image_url: "/images/offer_toys.webp",
    tag_id: "toys",
    link: "/catalog?shop=yesfancy&category=toys"
  },
  {
    id: "slide_lunchbox",
    title: "MODERN LUNCH BOXES",
    subtitle: "Insulated food carriers, stylish lunch sets & travel containers.",
    image_url: "/images/offer_lunch_boxes.webp",
    tag_id: "lunchbox",
    link: "/catalog?shop=yesfancy&category=lunchbox"
  }
];

export const ORIGINAL_YESFANCY_CATEGORIES = [
  { id: 'all', label: 'All Products', sort_order: 0 },
  { id: 'fashion', label: 'Beauty & Lifestyle', sort_order: 1 },
  { id: 'novelties', label: 'Gift Store', sort_order: 2 },
  { id: 'decor', label: 'Home & Decor', sort_order: 3 },
  { id: 'games', label: 'Games', sort_order: 4 },
  { id: 'toys', label: 'Toys', sort_order: 5 },
  { id: 'lunchbox', label: 'Lunch Boxes', sort_order: 6 }
];

export async function getShopConfigAsync(slug: string) {
  const supabase = getSupabaseClient();
  if (!supabase) return null;

  try {
    const { data: shopRecord, error } = await supabase
      .from('shops')
      .select('*')
      .eq('slug', slug)
      .single();

    if (error || !shopRecord) return null;

    // Fetch products belonging to this shop
    const { data: products } = await supabase
      .from('products')
      .select('*')
      .eq('shop_id', shopRecord.id);

    // Fetch structured categories from categories table
    const { data: dbCategories } = await supabase
      .from('categories')
      .select('*')
      .eq('shop_id', shopRecord.id)
      .order('sort_order', { ascending: true });

    let tagList = [];
    if (slug === 'yesfancy') {
      tagList = ORIGINAL_YESFANCY_CATEGORIES;
    } else if (dbCategories && dbCategories.length > 0) {
      tagList = dbCategories.map(c => ({
        id: c.id,
        label: c.label,
        sort_order: c.sort_order
      }));
    } else {
      const categoryMap = new Map<string, string>();
      categoryMap.set('all', 'All Products');
      (products || []).forEach((p: any) => {
        if (p.category_id && p.category_id !== 'all') {
          categoryMap.set(p.category_id, formatTagLabel(p.category_id));
        }
      });
      tagList = Array.from(categoryMap.entries()).map(([id, label], index) => ({
        id,
        label,
        sort_order: index
      }));
    }

    const themeObj = shopRecord.theme || {};

    return {
      shop: {
        id: shopRecord.id,
        slug: shopRecord.slug,
        name: shopRecord.name,
        tagline: shopRecord.tagline,
        category: shopRecord.category,
        template: shopRecord.template_key || 'gift_shop_template_1',
        phone: shopRecord.phone,
        announcement_text: shopRecord.announcement_text || 'FREE SHIPPING ON ORDERS ABOVE ₹999 | EXPRESS STORE PICKUP',
        logo_url: shopRecord.logo_url || '/images/yes_fancy_icon_transparent.png',
        logo_animated_url: shopRecord.logo_animated_url || '/images/yes_fancy_icon_animated.gif',
        logo_text: shopRecord.logo_text || shopRecord.name,
        features_ticker: shopRecord.features_ticker || [
          { label: "Easy Return", icon: "return" },
          { label: "Quality Assured", icon: "quality" },
          { label: "Satisfied Customers", icon: "heart" },
          { label: "Express Dispatch", icon: "dispatch" }
        ],
        hero_slides: (shopRecord.hero_slides && shopRecord.hero_slides.length > 0) ? shopRecord.hero_slides : defaultOfferSlides,
        theme: {
          primary_color: themeObj.primary_color || '#581C87',
          secondary_color: themeObj.secondary_color || '#D4AF37',
          accent_color: themeObj.accent_color || '#E11D48',
          font_title: themeObj.font_title || 'Plus Jakarta Sans',
          font_body: themeObj.font_body || 'Plus Jakarta Sans'
        },
        tags: tagList,
        categories: tagList,
        products: (products || []).map((p: any) => ({
          ...p,
          image_url: p.image_url || ''
        })),
        carousels: {
          hero: (shopRecord.hero_slides && shopRecord.hero_slides.length > 0) ? shopRecord.hero_slides : defaultOfferSlides
        }
      }
    };
  } catch (e) {
    console.error('Error fetching shop config:', e);
    return null;
  }
}

export async function getAllShopsConfigAsync() {
  const supabase = getSupabaseClient();
  if (!supabase) return [];

  try {
    const { data: shops, error } = await supabase.from('shops').select('*');
    if (error || !shops) return [];

    const { data: allProducts } = await supabase.from('products').select('*');
    const { data: allDBCategories } = await supabase.from('categories').select('*').order('sort_order', { ascending: true });

    return shops.map(shopRecord => {
      const shopProducts = (allProducts || []).filter(p => p.shop_id === shopRecord.id);

      let tagList = [];
      if (shopRecord.slug === 'yesfancy') {
        tagList = ORIGINAL_YESFANCY_CATEGORIES;
      } else {
        const shopDBCats = (allDBCategories || []).filter(c => c.shop_id === shopRecord.id);
        if (shopDBCats.length > 0) {
          tagList = shopDBCats.map(c => ({
            id: c.id,
            label: c.label,
            sort_order: c.sort_order
          }));
        } else {
          const categoryMap = new Map<string, string>();
          categoryMap.set('all', 'All Products');
          shopProducts.forEach((p: any) => {
            if (p.category_id && p.category_id !== 'all') {
              categoryMap.set(p.category_id, formatTagLabel(p.category_id));
            }
          });
          tagList = Array.from(categoryMap.entries()).map(([id, label], index) => ({
            id,
            label,
            sort_order: index
          }));
        }
      }

      const themeObj = shopRecord.theme || {};

      return {
        id: shopRecord.id,
        slug: shopRecord.slug,
        name: shopRecord.name,
        tagline: shopRecord.tagline,
        category: shopRecord.category,
        template: shopRecord.template_key || 'gift_shop_template_1',
        phone: shopRecord.phone,
        announcement_text: shopRecord.announcement_text || 'FREE SHIPPING ON ORDERS ABOVE ₹999 | EXPRESS STORE PICKUP',
        logo_url: shopRecord.logo_url || '/images/yes_fancy_icon_transparent.png',
        logo_animated_url: shopRecord.logo_animated_url || '/images/yes_fancy_icon_animated.gif',
        logo_text: shopRecord.logo_text || shopRecord.name,
        features_ticker: shopRecord.features_ticker || [
          { label: "Easy Return", icon: "return" },
          { label: "Quality Assured", icon: "quality" },
          { label: "Satisfied Customers", icon: "heart" },
          { label: "Express Dispatch", icon: "dispatch" }
        ],
        hero_slides: (shopRecord.hero_slides && shopRecord.hero_slides.length > 0) ? shopRecord.hero_slides : defaultOfferSlides,
        theme: {
          primary_color: themeObj.primary_color || '#581C87',
          secondary_color: themeObj.secondary_color || '#D4AF37',
          accent_color: themeObj.accent_color || '#E11D48',
          font_title: themeObj.font_title || 'Plus Jakarta Sans',
          font_body: themeObj.font_body || 'Plus Jakarta Sans'
        },
        tags: tagList,
        categories: tagList,
        products: shopProducts.map((p: any) => ({
          ...p,
          image_url: p.image_url || ''
        })),
        carousels: {
          hero: (shopRecord.hero_slides && shopRecord.hero_slides.length > 0) ? shopRecord.hero_slides : defaultOfferSlides
        }
      };
    });
  } catch (e) {
    console.error('Error fetching all shops:', e);
    return [];
  }
}
