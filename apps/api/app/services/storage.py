import os
import zipfile
import shutil
import git
from supabase import create_client
from ..config import settings

class StorageService:
    def __init__(self):
        self.supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        
    def download_and_extract(self, storage_path: str) -> str:
        """
        Downloads a ZIP from Supabase Storage, extracts it, and returns the extraction directory.
        OR Clones a Git Repository if URL is provided.
        """
        storage_path = storage_path.strip()
        print(f"[STORAGE] Processing path: '{storage_path}'", flush=True)
        
        # 1. Check if it's a Git URL
        if storage_path.lower().startswith("http://") or storage_path.lower().startswith("https://"):
            print("[STORAGE] Detected Git URL. Cloning...", flush=True)
            return self.clone_repo(storage_path)

        local_zip_path = os.path.join(settings.UPLOAD_DIR, os.path.basename(storage_path))
        extract_dir = os.path.join(settings.UPLOAD_DIR, os.path.splitext(os.path.basename(storage_path))[0])
        
        # Local File/Directory Support for Testing
        if storage_path.startswith("local://") or os.path.isabs(storage_path):
            source_path = storage_path.replace("local://", "")
            print(f"[STORAGE] Using local source: {source_path}")
            if not os.path.exists(source_path):
                 raise Exception(f"Local path not found: {source_path}")
            
            # If it's already a directory, just return it
            if os.path.isdir(source_path):
                print(f"[STORAGE] Path is a directory, using as is: {source_path}")
                return source_path
                
            # If it's a file, copy to temp and treat as ZIP
            shutil.copy(source_path, local_zip_path)
        else:
            print(f"Downloading {storage_path} to {local_zip_path}...")
            
            # Download from Supabase
            # Bucket is 'source-code' based on frontend logic
            bucket_name = "source-code"
            try:
                with open(local_zip_path, 'wb+') as f:
                    res = self.supabase.storage.from_(bucket_name).download(storage_path)
                    f.write(res)
            except Exception as e:
                print(f"Error downloading file: {e}")
                raise e
            
        print(f"Extracting to {extract_dir}...")
        
        # Extract
        if not os.path.exists(extract_dir):
            os.makedirs(extract_dir)
            
        try:
            with zipfile.ZipFile(local_zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        except zipfile.BadZipFile:
             print("Error: The downloaded file is not a valid ZIP.")
             raise Exception("Invalid ZIP file")
             
        # Cleanup ZIP
        os.remove(local_zip_path)
        
        return extract_dir

    def clone_repo(self, repo_url: str) -> str:
        """
        Clones a public git repository to a temporary directory.
        If the URL points to a specific GitHub file (blob), it downloads that single file.
        """
        import time
        import httpx
        
        # Case A: GitHub File (Blob) -> Download Single File
        if "github.com" in repo_url and "/blob/" in repo_url:
            print(f"[STORAGE] Detected GitHub File URL: {repo_url}")
            # Convert to Raw URL
            # From: https://github.com/user/repo/blob/branch/folder/file.ext
            # To:   https://raw.githubusercontent.com/user/repo/branch/folder/file.ext
            raw_url = repo_url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
            
            filename = repo_url.split('/')[-1]
            # Unique folder
            repo_dir_name = f"single_file_{int(time.time())}"
            target_dir = os.path.join(settings.UPLOAD_DIR, repo_dir_name)
            os.makedirs(target_dir, exist_ok=True)
            target_path = os.path.join(target_dir, filename)
            
            print(f"[STORAGE] Downloading raw file from {raw_url}...")
            try:
                with httpx.Client() as client:
                    resp = client.get(raw_url, follow_redirects=True)
                    resp.raise_for_status()
                    with open(target_path, "wb") as f:
                        f.write(resp.content)
                print(f"[STORAGE] File downloaded to {target_path}")
                return target_dir
            except Exception as e:
                print(f"[ERROR] Failed to download raw file: {e}")
                raise Exception(f"Could not download file from GitHub: {str(e)}")

        # Case B: Standard Git Repo -> Clone
        # Create a safe folder name from the URL
        repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
        # Add a timestamp or random string to avoid collisions if analyzing same repo multiple times
        repo_dir_name = f"{repo_name}_{int(time.time())}"
        clone_dir = os.path.join(settings.UPLOAD_DIR, repo_dir_name)
        
        print(f"Cloning {repo_url} to {clone_dir}...")
        
        if os.path.exists(clone_dir):
            shutil.rmtree(clone_dir)
            
        try:
            git.Repo.clone_from(repo_url, clone_dir)
            print("Clone successful.")
            return clone_dir
        except git.exc.GitCommandError as ge:
            # Handle Windows "checkout failed" errors (exit code 128) due to invalid filenames (e.g. colons)
            # If the .git directory exists, we assume the repo was downloaded but some files failed to extract.
            # We proceed with the files that ARE valid.
            if ge.status == 128 and os.path.exists(os.path.join(clone_dir, '.git')):
                 print(f"[WARNING] Clone finished with checkout errors (likely Windows path compatibility). Continuing with available files. Details: {ge}", flush=True)
                 return clone_dir
            else:
                 print(f"[ERROR] Git Clone Failed: {ge}", flush=True)
                 raise ge
        except Exception as e:
            print(f"Error cloning repository: {e}", flush=True)
            raise e

    def walk_files(self, root_dir: str):
        """
        Yields file paths and contents for relevant files.
        """
        ignore_dirs = {'.git', 'node_modules', '__pycache__', '.next', 'venv', 'env'}
        valid_extensions = {'.sql', '.py', '.json', '.xml', '.dtsx', '.md', '.yml', '.yaml'}
        
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # Modify dirnames in-place to skip ignored directories
            dirnames[:] = [d for d in dirnames if d not in ignore_dirs]
            
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext in valid_extensions:
                    full_path = os.path.join(dirpath, filename)
                    try:
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        yield full_path, content, ext
                    except Exception as e:
                        print(f"Error reading file {filename}: {e}")
                        continue