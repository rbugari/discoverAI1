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
        Supports local paths for testing if prefixed with 'local://' or absolute paths.
        """
        local_zip_path = os.path.join(settings.UPLOAD_DIR, os.path.basename(storage_path))
        extract_dir = os.path.join(settings.UPLOAD_DIR, os.path.splitext(os.path.basename(storage_path))[0])
        
        # Local File Support for Testing
        if storage_path.startswith("local://") or os.path.isabs(storage_path):
            source_path = storage_path.replace("local://", "")
            print(f"Using local file: {source_path}")
            if not os.path.exists(source_path):
                 raise Exception(f"Local file not found: {source_path}")
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
        """
        # Create a safe folder name from the URL
        repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
        # Add a timestamp or random string to avoid collisions if analyzing same repo multiple times
        import time
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
                 print(f"[WARNING] Clone finished with checkout errors (likely Windows path compatibility). Continuing with available files. Details: {ge}")
                 return clone_dir
            else:
                 print(f"[ERROR] Git Clone Failed: {ge}")
                 raise ge
        except Exception as e:
            print(f"Error cloning repository: {e}")
            raise e

    def walk_files(self, root_dir: str):
        """
        Yields file paths and contents for relevant files.
        """
        ignore_dirs = {'.git', 'node_modules', '__pycache__', '.next', 'venv', 'env'}
        valid_extensions = {'.sql', '.py', '.json', '.xml', '.dtsx'}
        
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