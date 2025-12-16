-- Skip 'storage.objects' policies if you don't have permission.
-- Instead, use the Supabase UI -> Storage -> Policies to add them manually if this script fails.
-- Or try creating policies ONLY for your public tables first.

-- 1. Solutions Table
ALTER TABLE public.solutions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow Anon Insert Solutions" ON public.solutions;
CREATE POLICY "Allow Anon Insert Solutions"
ON public.solutions
FOR INSERT
TO public
WITH CHECK (true);

DROP POLICY IF EXISTS "Allow Anon Select Solutions" ON public.solutions;
CREATE POLICY "Allow Anon Select Solutions"
ON public.solutions
FOR SELECT
TO public
USING (true);

DROP POLICY IF EXISTS "Allow Anon Update Solutions" ON public.solutions;
CREATE POLICY "Allow Anon Update Solutions"
ON public.solutions
FOR UPDATE
TO public
USING (true);

-- 2. Organizations Table
ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow Anon Insert Orgs" ON public.organizations;
CREATE POLICY "Allow Anon Insert Orgs"
ON public.organizations
FOR INSERT
TO public
WITH CHECK (true);

DROP POLICY IF EXISTS "Allow Anon Select Orgs" ON public.organizations;
CREATE POLICY "Allow Anon Select Orgs"
ON public.organizations
FOR SELECT
TO public
USING (true);

-- 3. Storage Policies (Try this part separately if it fails)
-- If you get "must be owner of table objects", do this in the UI:
-- Go to Storage -> Policies -> 'source-code' bucket -> New Policy -> "Give full access to everyone"
