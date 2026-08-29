export const prerender = false;

import type { APIRoute } from 'astro';
import { supabase, isSupabaseConfigured } from '@lib/supabase';

export const GET: APIRoute = async ({ url }) => {
  const shopSlug = url.searchParams.get('shop');
  if (!shopSlug) {
    return new Response(JSON.stringify({ error: 'Missing shop parameter' }), { status: 400 });
  }

  if (isSupabaseConfigured && supabase) {
    const { data: orders, error } = await supabase
      .from('orders')
      .select('*')
      .eq('shop_slug', shopSlug)
      .order('created_at', { ascending: false });

    if (!error) {
      return new Response(JSON.stringify({ orders }), { status: 200 });
    }
  }

  return new Response(JSON.stringify({ orders: [] }), { status: 200 });
};

export const POST: APIRoute = async ({ request }) => {
  try {
    const body = await request.json();
    const { order_id, shop_slug, customer_name, phone, address, items, total } = body;

    if (isSupabaseConfigured && supabase) {
      // Find shop_id
      const { data: shopRecord } = await supabase
        .from('shops')
        .select('id')
        .eq('slug', shop_slug)
        .single();

      if (shopRecord) {
        const { data, error } = await supabase
          .from('orders')
          .upsert({
            order_id,
            shop_id: shopRecord.id,
            shop_slug,
            customer_name,
            phone,
            address,
            items,
            total,
            status: 'Order Placed & Processing'
          }, { onConflict: 'order_id' })
          .select()
          .single();

        if (!error) {
          return new Response(JSON.stringify({ success: true, order: data }), { status: 200 });
        }
      }
    }

    return new Response(JSON.stringify({ success: true }), { status: 200 });
  } catch (e: any) {
    return new Response(JSON.stringify({ error: e.message }), { status: 500 });
  }
};
