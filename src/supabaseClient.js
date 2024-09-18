import { createClient } from '@supabase/supabase-js';
import { keys } from './creds';
// Add your Supabase API URL and Anon Key
const supabaseUrl = keys.API_URL;
const supabaseAnonKey = keys.API_KEY;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
