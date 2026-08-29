export const prerender = false;

import type { APIRoute } from 'astro';
import { supabase, isSupabaseConfigured } from '@lib/supabase';
import { uploadTenantAsset } from '@lib/storage';

export const POST: APIRoute = async ({ request }) => {
  try {
    const body = await request.json();
    const { 
      slug, 
      name,
      template_key, 
      phone, 
      announcement_text, 
      tagline,
      logo_url,
      primary_color, 
      secondary_color, 
      accent_color,
      font_title,
      font_body 
    } = body;

    if (!slug) {
      return new Response(JSON.stringify({ error: 'Missing shop slug' }), { status: 400 });
    }

    let publicLogoUrl = logo_url;
    if (logo_url && logo_url.startsWith('data:image')) {
      publicLogoUrl = await uploadTenantAsset(slug, 'banners', logo_url, `logo_${Date.now()}`);
    }

    if (isSupabaseConfigured && supabase) {
      // 1. Update Shop record
      const updatePayload: any = {
        template_key,
        phone,
        announcement_text,
        tagline
      };
      if (name) updatePayload.name = name;

      const { data: shopRecord, error: shopError } = await supabase
        .from('shops')
        .update(updatePayload)
        .eq('slug', slug)
        .select()
        .single();

      if (shopError || !shopRecord) {
        return new Response(JSON.stringify({ error: shopError?.message }), { status: 400 });
      }

      // 2. Update or Insert Shop Theme
      const { error: themeError } = await supabase
        .from('shop_themes')
        .upsert({
          shop_id: shopRecord.id,
          primary_color: primary_color || '#00A896',
          secondary_color: secondary_color || '#F4F4F9',
          accent_color: accent_color || '#E63946',
          font_title: font_title || 'Playfair Display',
          font_body: font_body || 'Montserrat'
        }, { onConflict: 'shop_id' });

      if (themeError) {
        return new Response(JSON.stringify({ error: themeError.message }), { status: 400 });
      }

      return new Response(JSON.stringify({ success: true }), { status: 200 });
    }

    return new Response(JSON.stringify({ success: true }), { status: 200 });
  } catch (e: any) {
    return new Response(JSON.stringify({ error: e.message }), { status: 500 });
  }
};
