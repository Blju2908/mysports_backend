from supabase import create_client, Client

url = "http://localhost:54321"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0"

supabase: Client = create_client(url, key)

# Testabfrage
response = supabase.table('showcase_waitlist').select("*").execute()
print(response)
