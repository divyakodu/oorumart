export const prerender = false;

import type { APIRoute } from 'astro';
import { supabase, isSupabaseConfigured } from '../../lib/supabase';
import { uploadTenantAsset } from '../../lib/storage';

export const POST: APIRoute = async ({ request }) => {
  try {
    const body = await request.json();
    const { shop_slug, id, label, tag, image_url } = body;

    if (!shop_slug || !label) {
      return new Response(JSON.stringify({ error: 'Missing required parameters' }), { status: 400 });
    }

    const catId = (id && typeof id === 'string' && id.trim().length > 0) ? id.trim() : `cat_${Date.now()}`;

    let publicCloudUrl = image_url;
    if (image_url && image_url.startsWith('data:image')) {
      publicCloudUrl = await uploadTenantAsset(shop_slug, 'categories', image_url, catId);
    }

    if (isSupabaseConfigured && supabase) {
      const { data: shopRecord } = await supabase
        .from('shops')
        .select('id')
        .eq('slug', shop_slug)
        .single();

      if (shopRecord) {
        let { error } = await supabase
          .from('categories')
          .upsert({
            id: catId,
            shop_id: shopRecord.id,
            label,
            tag: tag || label.toLowerCase().replace(/\s+/g, '_'),
            image_url: publicCloudUrl || '/images/hero_banner.jpg'
          });

        if (error && error.message.includes('tag')) {
          // Schema compatibility fallback if 'tag' column is not in DB table
          const res = await supabase
            .from('categories')
            .upsert({
              id: catId,
              shop_id: shopRecord.id,
              label,
              image_url: publicCloudUrl || '/images/hero_banner.jpg'
            });
          error = res.error;
        }

        if (!error) {
          return new Response(JSON.stringify({ success: true, image_url: publicCloudUrl, id: catId }), { status: 200 });
        } else {
          return new Response(JSON.stringify({ error: error.message }), { status: 400 });
        }
      }
    }

    return new Response(JSON.stringify({ success: true, image_url: publicCloudUrl, id: catId }), { status: 200 });
  } catch (e: any) {
    return new Response(JSON.stringify({ error: e.message }), { status: 500 });
  }
};

export const DELETE: APIRoute = async ({ request }) => {
  try {
    const url = new URL(request.url);
    const id = url.searchParams.get('id');
    const shop_slug = url.searchParams.get('shop');

    if (!id || !shop_slug) {
      return new Response(JSON.stringify({ error: 'Missing id or shop parameter' }), { status: 400 });
    }

    if (isSupabaseConfigured && supabase) {
      const { data: shopRecord } = await supabase
        .from('shops')
        .select('id')
        .eq('slug', shop_slug)
        .single();

      if (shopRecord) {
        const { error } = await supabase
          .from('categories')
          .delete()
          .eq('id', id)
          .eq('shop_id', shopRecord.id);

        if (error) {
          return new Response(JSON.stringify({ error: error.message }), { status: 400 });
        }
      }
    }

    return new Response(JSON.stringify({ success: true, id }), { status: 200 });
  } catch (e: any) {
    return new Response(JSON.stringify({ error: e.message }), { status: 500 });
  }
};

