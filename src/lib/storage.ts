import { createClient } from '@supabase/supabase-js';

const getEnvVar = (name: string): string => {
  try {
    if (typeof process !== 'undefined' && process.env && process.env[name]) {
      return process.env[name] as string;
    }
  } catch (e) {}
  try {
    if (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env[name]) {
      return import.meta.env[name] as string;
    }
  } catch (e) {}
  return '';
};

const supabaseUrl = getEnvVar('PUBLIC_SUPABASE_URL');
const serviceRoleKey = getEnvVar('SUPABASE_SERVICE_ROLE_KEY') || getEnvVar('PUBLIC_SUPABASE_ANON_KEY');

const supabaseAdmin = Boolean(supabaseUrl && serviceRoleKey)
  ? createClient(supabaseUrl, serviceRoleKey)
  : null;

/**
 * Uploads a product/category/banner image to Supabase Storage isolated by merchant shop slug.
 * Folder Path Structure: product-images/{shopSlug}/{folder}/{filename}
 */
export async function uploadTenantAsset(
  shopSlug: string,
  folder: 'products' | 'categories' | 'banners',
  fileDataUrl: string,
  filename?: string
): Promise<string> {
  if (!supabaseAdmin) {
    console.warn('Supabase admin client not initialized, returning raw data URL');
    return fileDataUrl;
  }

  try {
    const bucketName = 'product-images';
    
    // Extract mime type and base64 content
    const matches = fileDataUrl.match(/^data:([^;]+);base64,([\s\S]+)$/);
    if (!matches) {
      return fileDataUrl; // Return original URL if already a public link
    }

    const mimeType = matches[1];
    let extension = mimeType.split('/')[1] || 'jpg';
    if (extension.includes('+')) extension = extension.split('+')[0];
    if (extension === 'jpeg') extension = 'jpg';
    const base64Data = matches[2].trim();

    // Convert base64 string to Buffer
    const buffer = Buffer.from(base64Data, 'base64');
    
    const uniqueName = filename ? `${filename}.${extension}` : `${Date.now()}_${Math.random().toString(36).slice(2, 7)}.${extension}`;
    const filePath = `${shopSlug.toLowerCase().trim()}/${folder}/${uniqueName}`;

    console.log(`☁️ Uploading asset to Supabase Storage: ${bucketName}/${filePath} (${buffer.length} bytes)...`);

    // Upload file using admin client with service role key (bypasses RLS)
    const { data: uploadData, error } = await supabaseAdmin.storage
      .from(bucketName)
      .upload(filePath, buffer, {
        contentType: mimeType,
        upsert: true
      });

    if (error) {
      console.error('❌ Supabase storage upload error:', error.message);
      return fileDataUrl;
    }

    // Retrieve public CDN URL
    const { data: publicUrlData } = supabaseAdmin.storage
      .from(bucketName)
      .getPublicUrl(filePath);

    console.log('✅ Supabase Storage CDN URL generated:', publicUrlData.publicUrl);
    return publicUrlData.publicUrl;
  } catch (e: any) {
    console.error('❌ Storage helper exception:', e.message);
    return fileDataUrl;
  }
}
