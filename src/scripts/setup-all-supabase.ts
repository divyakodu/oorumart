import fs from 'fs';
import path from 'path';
import { Client } from 'pg';
import { supabase, isSupabaseConfigured } from '../lib/supabase';

async function setupAll() {
  console.log('----------------------------------------------------');
  console.log('🚀 FULLY AUTOMATED SUPABASE DATABASE SETUP & SEEDER');
  console.log('----------------------------------------------------');

  const supabaseUrl = process.env.PUBLIC_SUPABASE_URL || '';
  const projectRef = supabaseUrl.replace('https://', '').split('.')[0];
  const dbPassword = process.env.SUPABASE_DB_PASSWORD || '';
  const accessToken = process.env.SUPABASE_ACCESS_TOKEN || '';

  const sqlFilePath = path.join(process.cwd(), 'supabase/schema.sql');
  const sqlContent = fs.readFileSync(sqlFilePath, 'utf8');

  let tablesCreated = false;

  // Method 1: Try Supabase Management API using Personal Access Token (sbp_...)
  if (accessToken && projectRef) {
    console.log('⚡ Attempting automated SQL execution via Supabase Management API...');
    try {
      const res = await fetch(`https://api.supabase.com/v1/projects/${projectRef}/database/query`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query: sqlContent })
      });

      if (res.ok) {
        console.log('✅ Tables, Indexes, and RLS policies created automatically via Supabase API!');
        tablesCreated = true;
      } else {
        const errText = await res.text();
        console.warn('⚠️ Management API call returned:', res.status, errText);
      }
    } catch (e: any) {
      console.warn('⚠️ Management API call failed:', e.message);
    }
  }

  // Method 2: Try Direct PostgreSQL TCP Connection using Database Password
  if (!tablesCreated && dbPassword && projectRef) {
    console.log('⚡ Attempting direct PostgreSQL TCP connection...');
    const connectionString = `postgres://postgres.${projectRef}:${encodeURIComponent(dbPassword)}@aws-0-ap-south-1.pooler.supabase.com:6543/postgres`;
    const client = new Client({ connectionString, ssl: { rejectUnauthorized: false } });

    try {
      await client.connect();
      await client.query(sqlContent);
      console.log('✅ Tables, Indexes, and RLS policies created automatically via Postgres connection!');
      tablesCreated = true;
      await client.end();
    } catch (e: any) {
      console.warn('⚠️ Postgres connection failed:', e.message);
      try { await client.end(); } catch (ignore) {}
    }
  }

  if (!tablesCreated) {
    console.error('❌ Could not automatically run schema.sql.');
    console.error('👉 Please provide SUPABASE_ACCESS_TOKEN (sbp_...) OR SUPABASE_DB_PASSWORD in your .env file.');
    console.error('----------------------------------------------------');
    process.exit(1);
  }

  // ----------------------------------------------------
  // STEP 2: SEED MERCHANT DATA INTO SUPABASE TABLES
  // ----------------------------------------------------
  if (!isSupabaseConfigured || !supabase) {
    console.error('❌ Supabase client is not initialized. Check your .env file.');
    process.exit(1);
  }

  console.log('\n📦 Seeding Merchant Data into Supabase Tables...');
  const shopsDir = path.join(process.cwd(), 'src/shops');
  const shopFiles = fs.readdirSync(shopsDir).filter(f => f.endsWith('.json'));

  for (const file of shopFiles) {
    const filePath = path.join(shopsDir, file);
    const rawData = fs.readFileSync(filePath, 'utf8');
    const { shop } = JSON.parse(rawData);

    console.log(` -> Processing Merchant: ${shop.name} (${shop.slug})...`);

    // 1. Upsert Shop
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
      console.error(` ❌ Error inserting shop ${shop.slug}:`, shopError);
      continue;
    }

    const shopId = shopRecord.id;

    // 2. Upsert Theme
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

    console.log(` ✅ ${shop.name} successfully inserted (${shop.products.length} products).`);
  }

  console.log('----------------------------------------------------');
  console.log('🎉 COMPLETE AUTOMATED SETUP & MIGRATION SUCCESSFUL!');
  console.log('----------------------------------------------------');
}

setupAll().catch(err => {
  console.error('Fatal Automated Setup Error:', err);
  process.exit(1);
});
