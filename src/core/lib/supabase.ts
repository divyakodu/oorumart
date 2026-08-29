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
const supabaseKey = getEnvVar('SUPABASE_SERVICE_ROLE_KEY') || getEnvVar('PUBLIC_SUPABASE_ANON_KEY');

export const isSupabaseConfigured = Boolean(supabaseUrl && supabaseKey && !supabaseUrl.includes('your-supabase-project'));

export const supabase = isSupabaseConfigured 
  ? createClient(supabaseUrl, supabaseKey) 
  : null;
