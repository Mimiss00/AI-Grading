// Import Supabase client library
import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';

// Initialize Supabase
const supabaseUrl = 'https://lqhrqxxcommsocgtigmp.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxxaHJxeHhjb21tc29jZ3RpZ21wIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDIxMzk3MDUsImV4cCI6MjA1NzcxNTcwNX0.cpWTuEG4Ms9Q_1lXcYnjLGrtW29ihfIFH9MCjwcWWUw';
const bucketName = "aigrading";
const supabase = createClient(supabaseUrl, supabaseKey);

console.log('Supabase initialized:', supabase); // Debugging

// Export the Supabase client for use in other scripts
export  { supabase, supabaseUrl, bucketName };