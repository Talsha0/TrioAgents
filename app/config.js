// Connection settings for the shared online database (Supabase).
//
// Fill these in from Supabase: Project Settings -> API (or "Connect").
//   supabaseUrl: the Project URL, like https://abcdefghijkl.supabase.co
//   supabaseKey: the "publishable" key (sb_publishable_...) or the legacy "anon public" key.
//
// Both values are meant to be public: they are visible to anyone who opens the site.
// What protects the data is the login plus the database rules in supabase/schema.sql.
// NEVER put the "secret" / "service_role" key here.
//
// Leave supabaseUrl empty to run without the online database (data stays in this browser only).
window.APP_CONFIG = {
  supabaseUrl: 'https://prqlodbdkrajgoevdpcm.supabase.co',
  supabaseKey: 'sb_publishable_hyLardE50NJpvOh-MQXsVA_P52D1rNh',

  // Login methods shown on the sign-in screen.
  loginWithGoogle: true,
  loginWithEmail: false
};
