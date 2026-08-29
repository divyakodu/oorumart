export const prerender = false;

import type { APIRoute } from 'astro';
import { supabase, isSupabaseConfigured } from '../../lib/supabase';
import { uploadTenantAsset } from '../../lib/storage';

export const POST: APIRoute = async ({ request }) => {
  try {
    const body = await request.json();
    const { shop_slug, id, name, price, mrp, category_id, badge, tags, image_url, stock } = body;

    if (!shop_slug) {
      return new Response(JSON.stringify({ error: 'Missing shop_slug' }), { status: 400 });
    }

    const prodId = id || `prod_${Date.now()}`;

    // Upload photo to Supabase Storage isolated under product-images/{shop_slug}/products/
    let publicCloudUrl = image_url;
    if (image_url && image_url.startsWith('data:image')) {
      publicCloudUrl = await uploadTenantAsset(shop_slug, 'products', image_url, prodId);
    }

    const stockQty = stock !== undefined ? Number(stock) : 100;

    if (isSupabaseConfigured && supabase) {
      const { data: shopRecord } = await supabase
        .from('shops')
        .select('id')
        .eq('slug', shop_slug)
        .single();

      if (shopRecord) {
        const { error } = await supabase
          .from('products')
          .upsert({
            id: prodId,
            shop_id: shopRecord.id,
            category_id,
            name,
            price: Number(price),
            mrp: Number(mrp || price),
            image_url: publicCloudUrl,
            badge: badge || null,
            tags: Array.isArray(tags) ? tags : [category_id],
            stock: stockQty,
            is_active: true
          }, { onConflict: 'id,shop_id' });

        if (!error) {
          return new Response(JSON.stringify({ success: true, id: prodId, image_url: publicCloudUrl, stock: stockQty }), { status: 200 });
        } else {
          return new Response(JSON.stringify({ error: error.message }), { status: 400 });
        }
      }
    }

    return new Response(JSON.stringify({ success: true, id: prodId, image_url: publicCloudUrl, stock: stockQty }), { status: 200 });
  } catch (e: any) {
    return new Response(JSON.stringify({ error: e.message }), { status: 500 });
  }
};

export const DELETE: APIRoute = async ({ request }) => {
  try {
    const url = new URL(request.url);
    let ids: string[] = [];
    let shop_slug = url.searchParams.get('shop');

    const queryId = url.searchParams.get('id');
    const queryIds = url.searchParams.get('ids');

    if (queryId) ids = [queryId];
    else if (queryIds) ids = queryIds.split(',').map(s => s.trim()).filter(Boolean);
    else {
      try {
        const body = await request.json();
        if (body.ids && Array.isArray(body.ids)) ids = body.ids;
        else if (body.id) ids = [body.id];
        if (body.shop_slug) shop_slug = body.shop_slug;
      } catch (e) {}
    }

    if (ids.length === 0 || !shop_slug) {
      return new Response(JSON.stringify({ error: 'Missing product ids or shop parameter' }), { status: 400 });
    }

    if (isSupabaseConfigured && supabase) {
      const { data: shopRecord } = await supabase
        .from('shops')
        .select('id')
        .eq('slug', shop_slug)
        .single();

      if (shopRecord) {
        const { error } = await supabase
          .from('products')
          .delete()
          .in('id', ids)
          .eq('shop_id', shopRecord.id);

        if (error) {
          return new Response(JSON.stringify({ error: error.message }), { status: 400 });
        }
      }
    }

    return new Response(JSON.stringify({ success: true, count: ids.length, ids }), { status: 200 });
  } catch (e: any) {
    return new Response(JSON.stringify({ error: e.message }), { status: 500 });
  }
};

export const PATCH: APIRoute = async ({ request }) => {
  try {
    const body = await request.json();
    const { shop_slug, id, ids, is_active, stock } = body;
    const targetIds = Array.isArray(ids) ? ids : (id ? [id] : []);

    if (targetIds.length === 0 || !shop_slug) {
      return new Response(JSON.stringify({ error: 'Missing required parameters' }), { status: 400 });
    }

    const updates: Record<string, any> = {};
    if (is_active !== undefined) updates.is_active = Boolean(is_active);
    if (stock !== undefined) updates.stock = Number(stock);

    if (isSupabaseConfigured && supabase) {
      const { data: shopRecord } = await supabase
        .from('shops')
        .select('id')
        .eq('slug', shop_slug)
        .single();

      if (shopRecord) {
        const { error } = await supabase
          .from('products')
          .update(updates)
          .in('id', targetIds)
          .eq('shop_id', shopRecord.id);

        if (error) {
          return new Response(JSON.stringify({ error: error.message }), { status: 400 });
        }
      }
    }

    return new Response(JSON.stringify({ success: true, count: targetIds.length, ids: targetIds, updates }), { status: 200 });
  } catch (e: any) {
    return new Response(JSON.stringify({ error: e.message }), { status: 500 });
  }
};

