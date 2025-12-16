-- Enable RLS on storage.objects (if not already enabled)
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- Policy to allow ANYONE (Anon) to upload to 'source-code' bucket
-- WARNING: This is for MVP/Dev only. In prod, restrict to authenticated users.
CREATE POLICY "Allow Anon Uploads"
ON storage.objects
FOR INSERT
TO public
WITH CHECK ( bucket_id = 'source-code' );

-- Policy to allow ANYONE to read from 'source-code' bucket
-- Needed for the backend to download the file
CREATE POLICY "Allow Anon Downloads"
ON storage.objects
FOR SELECT
TO public
USING ( bucket_id = 'source-code' );

-- Also need policies for the 'solutions' table if inserting there failed too
-- (The error message might refer to the 'solutions' table insert or the storage upload)
-- Let's fix 'solutions' table just in case.

ALTER TABLE public.solutions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow Anon Insert Solutions"
ON public.solutions
FOR INSERT
TO public
WITH CHECK (true);

CREATE POLICY "Allow Anon Select Solutions"
ON public.solutions
FOR SELECT
TO public
USING (true);

CREATE POLICY "Allow Anon Update Solutions"
ON public.solutions
FOR UPDATE
TO public
USING (true);

-- Same for organizations
ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow Anon Insert Orgs"
ON public.organizations
FOR INSERT
TO public
WITH CHECK (true);

CREATE POLICY "Allow Anon Select Orgs"
ON public.organizations
FOR SELECT
TO public
USING (true);
