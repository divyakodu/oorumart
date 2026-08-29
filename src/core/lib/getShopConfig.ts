import { createClient } from '@supabase/supabase-js';

function getSupabaseClient() {
  const url = (typeof import.meta !== 'undefined' && import.meta.env ? import.meta.env.PUBLIC_SUPABASE_URL : null) || process.env.PUBLIC_SUPABASE_URL || '';
  const key = (typeof import.meta !== 'undefined' && import.meta.env ? (import.meta.env.SUPABASE_SERVICE_ROLE_KEY || import.meta.env.PUBLIC_SUPABASE_ANON_KEY) : null) || process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.PUBLIC_SUPABASE_ANON_KEY || '';

  if (url && key) {
    return createClient(url, key);
  }
  return null;
}

const tagLabelMap: Record<string, string> = {
  all: 'All Products',
  gift_store: 'Gift Store',
  home_decor: 'Home & Decor',
  bags_travel: 'Bags & Travel',
  board_games: 'Board Games',
  action_toys: 'Action Toys',
  lunch_boxes: 'Lunch Boxes',
  curated: 'Curated'
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
    id: "slide_gift_store",
    title: "FESTIVE GIFT GUIDE",
    subtitle: "Curated luxury hampers, fancy boxes & novelties for every occasion.",
    image_url: "/images/offer_gift_store.jpg",
    tag_id: "gift_store",
    link: "/catalog?shop=yesfancy&tag=gift_store"
  },
  {
    id: "slide_home_decor",
    title: "MODERN HOME & DECOR",
    subtitle: "Fancy minimal interiors, designer lamps & contemporary living accents.",
    image_url: "/images/offer_home_decor.jpg",
    tag_id: "home_decor",
    link: "/catalog?shop=yesfancy&tag=home_decor"
  },
  {
    id: "slide_bags_travel",
    title: "MODERN BAGS & TRAVEL",
    subtitle: "Sleek designer duffels, premium backpacks & modern travel gear.",
    image_url: "/images/offer_bags_travel.jpg",
    tag_id: "bags_travel",
    link: "/catalog?shop=yesfancy&tag=bags_travel"
  },
  {
    id: "slide_board_games",
    title: "BOARD GAMES",
    subtitle: "Sleek contemporary chess sets & modern tabletop board games.",
    image_url: "/images/offer_board_games.jpg",
    tag_id: "board_games",
    link: "/catalog?shop=yesfancy&tag=board_games"
  },
  {
    id: "slide_action_toys",
    title: "GAMES & TOYS",
    subtitle: "Modern action figures, sleek gaming gadgets & premium collectibles.",
    image_url: "https://images.unsplash.com/photo-1566576912321-d58ddd7a6088?q=80&w=2000&auto=format&fit=crop",
    tag_id: "action_toys",
    link: "/catalog?shop=yesfancy&tag=action_toys"
  },
  {
    id: "slide_lunch_boxes",
    title: "MODERN FOOD CARRIERS",
    subtitle: "Sleek double-walled insulated vacuum bento tiffins & smart lunchware.",
    image_url: "https://images.unsplash.com/photo-1584269600464-37b1b58a9fe7?q=80&w=2000&auto=format&fit=crop",
    tag_id: "lunch_boxes",
    link: "/catalog?shop=yesfancy&tag=lunch_boxes"
  }
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

    // Dynamically derive unique tags from product catalog
    const rawTagsSet = new Set<string>();
    (products || []).forEach((p: any) => {
      if (Array.isArray(p.tags)) {
        p.tags.forEach((t: string) => {
          if (t && t !== 'curated') rawTagsSet.add(t);
        });
      }
    });

    const uniqueTags = Array.from(rawTagsSet);
    
    // Sort tags consistently
    const tagOrder = ['gift_store', 'home_decor', 'bags_travel', 'board_games', 'action_toys', 'lunch_boxes'];
    uniqueTags.sort((a, b) => {
      const idxA = tagOrder.indexOf(a);
      const idxB = tagOrder.indexOf(b);
      if (idxA !== -1 && idxB !== -1) return idxA - idxB;
      if (idxA !== -1) return -1;
      if (idxB !== -1) return 1;
      return a.localeCompare(b);
    });

    const tagList = [
      { id: 'all', label: 'All Products', sort_order: 0 },
      ...uniqueTags.map((tag: string, index: number) => ({
        id: tag,
        label: formatTagLabel(tag),
        sort_order: index + 1
      }))
    ];

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
          { label: "1M+ Happy Customers", icon: "heart" },
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
        products: products || [],
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

    return shops.map(shopRecord => {
      const shopProducts = (allProducts || []).filter(p => p.shop_id === shopRecord.id);

      const rawTagsSet = new Set<string>();
      shopProducts.forEach((p: any) => {
        if (Array.isArray(p.tags)) {
          p.tags.forEach((t: string) => {
            if (t && t !== 'curated') rawTagsSet.add(t);
          });
        }
      });

      const uniqueTags = Array.from(rawTagsSet);
      const tagList = [
        { id: 'all', label: 'All Products', sort_order: 0 },
        ...uniqueTags.map((tag: string, index: number) => ({
          id: tag,
          label: formatTagLabel(tag),
          sort_order: index + 1
        }))
      ];

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
          { label: "1M+ Happy Customers", icon: "heart" },
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
        products: shopProducts,
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
