export const prerender = false;

import type { APIRoute } from 'astro';
import { supabase, isSupabaseConfigured } from '../../lib/supabase';
import { uploadTenantAsset } from '../../lib/storage';

export const POST: APIRoute = async ({ request }) => {
  try {
    const body = await request.json();
    const { shop_slug, title, subtitle, bg_gradient, cta_text, cta_link, image_url } = body;

    if (!shop_slug) {
      return new Response(JSON.stringify({ error: 'Missing shop_slug' }), { status: 400 });
    }

    let publicCloudUrl = image_url;
    if (image_url && image_url.startsWith('data:image')) {
      publicCloudUrl = await uploadTenantAsset(shop_slug, 'banners', image_url, `hero_${Date.now()}`);
    }

    if (isSupabaseConfigured && supabase) {
      const { data: shopRecord } = await supabase
        .from('shops')
        .select('id')
        .eq('slug', shop_slug)
        .single();

      if (shopRecord) {
        const { error } = await supabase
          .from('hero_slides')
          .insert({
            shop_id: shopRecord.id,
            title,
            subtitle,
            bg_gradient: bg_gradient || 'from-slate-900 to-teal-900',
            cta_text: cta_text || 'Explore Collection',
            cta_link: cta_link || 'all',
            image_url: publicCloudUrl,
            sort_order: 0
          });

        if (!error) {
          return new Response(JSON.stringify({ success: true }), { status: 200 });
        } else {
          return new Response(JSON.stringify({ error: error.message }), { status: 400 });
        }
      }
    }

    return new Response(JSON.stringify({ success: true }), { status: 200 });
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
          .from('hero_slides')
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

