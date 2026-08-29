import fs from 'fs';
import path from 'path';
import { supabase, isSupabaseConfigured } from '../lib/supabase';

async function seedSupabase() {
  console.log('----------------------------------------------------');
  console.log('🚀 OORUMART SUPABASE DATA SEEDER');
  console.log('----------------------------------------------------');

  if (!isSupabaseConfigured || !supabase) {
    console.error('❌ Supabase is NOT configured yet!');
    console.error('👉 Please populate PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in your .env file.');
    console.error('----------------------------------------------------');
    process.exit(1);
  }

  const shopsDir = path.join(process.cwd(), 'src/shops');
  const shopFiles = fs.readdirSync(shopsDir).filter(f => f.endsWith('.json'));

  for (const file of shopFiles) {
    const filePath = path.join(shopsDir, file);
    const rawData = fs.readFileSync(filePath, 'utf8');
    const { shop } = JSON.parse(rawData);

    console.log(`📦 Seeding Merchant: ${shop.name} (${shop.slug})...`);

    // 1. Upsert Shop Record
    const { data: shopRecord, error: shopError } = await supabase
      .from('shops')
      .upsert({
        slug: shop.slug,
        name: shop.name,
        tagline: shop.tagline || '',
        category: shop.category,
        template_key: shop.template || 'gift_shop_template_1',
        phone: shop.phone,
        announcement_text: shop.announcement_text || ''
      }, { onConflict: 'slug' })
      .select()
      .single();

    if (shopError || !shopRecord) {
      console.error(`❌ Error upserting shop ${shop.slug}:`, shopError);
      continue;
    }

    const shopId = shopRecord.id;

    // 2. Upsert Theme Record
    if (shop.theme) {
      await supabase
        .from('shop_themes')
        .upsert({
          shop_id: shopId,
          primary_color: shop.theme.primary_color,
          secondary_color: shop.theme.secondary_color || '#F4F4F9',
          accent_color: shop.theme.accent_color || '#E63946',
          font_title: shop.theme.font_family_title || 'Playfair Display',
          font_body: shop.theme.font_family_body || 'Montserrat'
        }, { onConflict: 'shop_id' });
    }

    // 3. Upsert Categories
    if (Array.isArray(shop.categories)) {
      const categoryRows = shop.categories.map((c: any, index: number) => ({
        id: c.id,
        shop_id: shopId,
        label: c.label,
        image_url: c.image_url || null,
        sort_order: index
      }));

      await supabase.from('categories').upsert(categoryRows, { onConflict: 'id,shop_id' });
    }

    // 4. Upsert Products
    if (Array.isArray(shop.products)) {
      const productRows = shop.products.map((p: any) => ({
        id: p.id,
        shop_id: shopId,
        category_id: p.category_id,
        name: p.name,
        description: p.description || '',
        price: p.price,
        mrp: p.mrp || p.price,
        image_url: p.image_url,
        stock: p.stock || 100,
        badge: p.badge || null,
        tags: p.tags || [p.category_id],
        is_active: true
      }));

      await supabase.from('products').upsert(productRows, { onConflict: 'id,shop_id' });
    }

    // 5. Upsert Hero Slides
    if (shop.carousels && Array.isArray(shop.carousels.hero)) {
      const slideRows = shop.carousels.hero.map((s: any, index: number) => ({
        shop_id: shopId,
        title: s.title,
        subtitle: s.subtitle,
        bg_gradient: s.bg_gradient,
        cta_text: s.cta_text,
        cta_link: s.cta_link,
        sort_order: index
      }));

      await supabase.from('hero_slides').upsert(slideRows);
    }

    console.log(`✅ ${shop.name} successfully seeded (${shop.products.length} products).`);
  }

  console.log('----------------------------------------------------');
  console.log('✨ All shops successfully migrated to Supabase Database!');
  console.log('----------------------------------------------------');
}

seedSupabase().catch(err => {
  console.error('Fatal Seeder Error:', err);
  process.exit(1);
});
