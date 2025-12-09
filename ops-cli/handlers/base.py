"""
Base handler interface for service creation.

All template handlers must inherit from this class.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
import os
import subprocess
from jinja2 import Environment, FileSystemLoader


@dataclass
class ServiceConfig:
    """Configuration for a service being created"""
    name: str
    template_id: str
    config: Dict[str, Any]
    base_dir: str = "/app"
    
    @property
    def namespace(self) -> str:
        """Kubernetes namespace for the service (defaults to service name for isolation)"""
        # Each service gets its own namespace by default
        return self.config.get("namespace", self.name)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value"""
        return self.config.get(key, default)


class BaseHandler(ABC):
    """Abstract base class for service handlers"""
    
    # Template ID this handler processes
    template_id: str = ""
    
    def __init__(self, service_config: ServiceConfig):
        self.service = service_config
        self.base_dir = service_config.base_dir
        self.templates_dir = os.path.join(self.base_dir, "ops-cli", "templates", self.get_template_subdir())
        
        # GitOps Directory (Persistent)
        self.gitops_repo_dir = os.environ.get("HUBBOPS_GITOPS_DIR", "/data/hubbops-infra")
        self._setup_jinja()
    
    def _setup_jinja(self):
        """Setup Jinja2 environment"""
        if os.path.exists(self.templates_dir):
            self.env = Environment(loader=FileSystemLoader(self.templates_dir))
        else:
            self.env = None
    
    @abstractmethod
    def get_template_subdir(self) -> str:
        """Return the template subdirectory name (e.g., 'python', 'go')"""
        pass
    
    @abstractmethod
    def validate(self) -> tuple[bool, list[str]]:
        """Validate configuration"""
        pass
    
    @abstractmethod
    def generate_code(self) -> str:
        """Generate application code"""
        pass
    
    @abstractmethod
    def generate_manifests(self) -> Dict[str, str]:
        """Generate Kubernetes manifests"""
        pass
    
    def get_image_name(self) -> str:
        """Get the Docker image name for this service"""
        from config import get_config
        cfg = get_config()
        return cfg.get_image_name(self.service.name, "v1.0")
    
    def build_image(self) -> bool:
        """Build Docker image for the service"""
        from config import get_config
        cfg = get_config()
        
        code_dir = os.path.join(self.base_dir, "apps", self.service.name)
        image_name = self.get_image_name()
        
        print(f"   Building image: {image_name}")
        result = subprocess.run(
            f"docker build -t {image_name} {code_dir}",
            shell=True,
            cwd=self.base_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"   ❌ Build failed: {result.stderr[:200]}")
            return False
        
        print(f"   ✅ Image built")
        return True
    
    def import_to_k3d(self) -> bool:
        """Import image to k3d cluster"""
        from config import get_config
        cfg = get_config()
        
        if not cfg.k3d_cluster:
            print("   ⚠️  No k3d cluster configured, skipping import")
            return True
        
        image_name = self.get_image_name()
        print(f"   Importing to k3d cluster: {cfg.k3d_cluster}")
        
        result = subprocess.run(
            f"k3d image import {image_name} -c {cfg.k3d_cluster}",
            shell=True,
            cwd=self.base_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"   ⚠️  Import failed (may not affect local dev): {result.stderr[:100]}")
            return False
        
        print(f"   ✅ Image imported")
        return True

    def _ensure_git_repo(self) -> bool:
        """Ensure GitOps repo is cloned and up to date"""
        from config import get_config
        cfg = get_config()
        repo_url = cfg.git_infra_repo 
        
        if not repo_url:
            print("   ⚠️  No Git infrastructure repository configured in settings.")
            return False

        # Convert HTTPS to SSH if needed
        # This allows users to paste browser URL but we use SSH key for auth
        if repo_url.startswith("https://github.com/"):
            # From: https://github.com/Diegohnunes/infra
            # To:   git@github.com:Diegohnunes/infra.git
            ssh_url = repo_url.replace("https://github.com/", "git@github.com:")
            if not ssh_url.endswith(".git"):
                ssh_url += ".git"
            print(f"   ℹ️  Converting HTTPS URL to SSH: {ssh_url}")
            repo_url = ssh_url

        if not os.path.exists(self.gitops_repo_dir):
            print(f"   Cloning infrastructure repo from {repo_url}...")
            
            # Debug: Check SSH setup
            ssh_cmd = os.environ.get("GIT_SSH_COMMAND")
            if ssh_cmd:
                print(f"   ℹ️  Using custom SSH command: {ssh_cmd}")
                # Extract key path if present
                import re
                key_match = re.search(r"-i\s+([^\s]+)", ssh_cmd)
                if key_match:
                    key_path = key_match.group(1)
                    if os.path.exists(key_path):
                        perms = oct(os.stat(key_path).st_mode)[-3:]
                        print(f"   🔑 Key file exists at {key_path} (Perms: {perms})")
                    else:
                        print(f"   ❌ Key file MISSING at {key_path}")

            try:
                os.makedirs(os.path.dirname(self.gitops_repo_dir), exist_ok=True)
                result = subprocess.run(
                    f"git clone {repo_url} {self.gitops_repo_dir}", 
                    shell=True,
                    capture_output=True, # Capture to print details manually
                    text=True
                )
                
                if result.returncode != 0:
                    print(f"   ❌ Git clone failed (Exit {result.returncode})")
                    print(f"   STDERR:\n{result.stderr}")
                    return False
                    
            except Exception as e:
                print(f"   ❌ Git clone failed with exception: {e}")
                return False
        else:
            print("   Pulling latest infrastructure changes...")
            try:
                subprocess.run("git pull", shell=True, cwd=self.gitops_repo_dir, check=True)
            except subprocess.CalledProcessError as e:
                print(f"   ⚠️  Git pull failed (ignoring): {e}")
        
        return True

    def _push_to_git(self) -> bool:
        """Commit and push changes to GitOps repo"""
        print("   Pushing changes to infrastructure repository...")
        try:
            # Config identity if needed
            subprocess.run("git config user.name 'HubbOps Bot'", shell=True, cwd=self.gitops_repo_dir)
            subprocess.run("git config user.email 'bot@hubbops.io'", shell=True, cwd=self.gitops_repo_dir)
            
            subprocess.run("git add .", shell=True, check=True, cwd=self.gitops_repo_dir)
            subprocess.run(f"git commit -m 'Add service {self.service.name}'", shell=True, check=True, cwd=self.gitops_repo_dir)
            subprocess.run("git push", shell=True, check=True, cwd=self.gitops_repo_dir)
            print("   ✅ Changes pushed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Git push failed: {e}")
            return False

    def deploy(self) -> bool:
        """Deploy to Kubernetes via ArgoCD"""
        # Ensure we are working with the git repo
        if not self._ensure_git_repo():
            print("   ⚠️  GitOps repo not available, falling back to local apply")
            # Fallback to local apply if git fails (legacy behavior)
            app_file = os.path.join(self.base_dir, "gitops", "apps", f"{self.service.name}.yaml")
            local_mode = True
        else:
            local_mode = False
            # Generate into the repo
            app_file = os.path.join(self.gitops_repo_dir, "gitops", "apps", f"{self.service.name}.yaml")

        if not os.path.exists(app_file):
            print(f"   ❌ ArgoCD app file not found: {app_file}")
            return False
        
        print(f"   Applying ArgoCD application manifest...")
        result = subprocess.run(
            f"kubectl apply -f {app_file}",
            shell=True,
            cwd=self.base_dir, # kubectl can run from anywhere
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"   ❌ Deploy failed: {result.stderr[:100]}")
            return False
            
        print(f"   ✅ ArgoCD application created")
        return True
    
    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render a Jinja2 template"""
        if not self.env:
            raise RuntimeError(f"Templates directory not found: {self.templates_dir}")
        
        template = self.env.get_template(template_name)
        return template.render(context)
    
    def write_file(self, output_dir: str, filename: str, content: str):
        """Write content to a file"""
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"   Created {filename}")
    
    def get_context(self) -> Dict[str, Any]:
        """Get the template context with common variables"""
        return {
            "name": self.service.name,
            "namespace": self.service.namespace,
            "image": self.get_image_name(),
            **self.service.config
        }
    
    def _generate_namespace_yaml(self, context: Dict[str, Any]) -> str:
        """Generate Namespace manifest for service isolation"""
        namespace = context["namespace"]
        name = context["name"]
        
        return f'''apiVersion: v1
kind: Namespace
metadata:
  name: {namespace}
  labels:
    app: {name}
    managed-by: hubbops
'''

    
    def _generate_argocd_app(self, context: Dict[str, Any]):
        """Generate ArgoCD Application"""
        name = context["name"]
        namespace = context["namespace"]
        from config import get_config
        cfg = get_config()
        
        repo_url = cfg.git_infra_repo or "https://github.com/YOUR_ORG/your-infra-repo"
        
        # Force SSH for private repos (ArgoCD needs SSH key)
        if "https://github.com/" in repo_url:
            repo_url = repo_url.replace("https://github.com/", "git@github.com:")
            print(f"ℹ️  Converted Repo URL for ArgoCD: {repo_url}")
        
        content = f'''apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: {name}
  namespace: argocd
spec:
  project: default
  source:
    repoURL: {repo_url}
    targetRevision: HEAD
    path: gitops/manifests/{name}
  destination:
    server: https://kubernetes.default.svc
    namespace: {namespace}
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
'''
        # Write to GitOps repo if available, else local
        if os.path.exists(self.gitops_repo_dir):
            apps_dir = os.path.join(self.gitops_repo_dir, "gitops", "apps")
        else:
            apps_dir = os.path.join(self.base_dir, "gitops", "apps")
            
        os.makedirs(apps_dir, exist_ok=True)
        self.write_file(apps_dir, f"{name}.yaml", content)

    def execute(self) -> bool:
        """Execute the full service creation pipeline"""
        print(f"\n{'='*60}")
        print(f"Creating {self.service.name} using {self.template_id} template")
        print(f"{'='*60}\n")
        
        # Step 1: Validate
        print("Step 1/6: Validating configuration...")
        is_valid, errors = self.validate()
        if not is_valid:
            for err in errors:
                print(f"   ❌ {err}")
            return False
        print("   ✅ Configuration valid")
        
        # Step 2: Generate code
        print("\nStep 2/6: Generating application code...")
        try:
            code_dir = self.generate_code()
            print(f"   ✅ Code generated in {code_dir}")
        except Exception as e:
            print(f"   ❌ Code generation failed: {e}")
            return False
        
        # Step 3: Generate manifests (and clone repo)
        print("\nStep 3/6: Preparing manifests...")
        self._ensure_git_repo() # Prepare repo
        
        try:
            manifests = self.generate_manifests()
            
            # Determine target dir (Repo or Local)
            if os.path.exists(self.gitops_repo_dir):
                target_base = self.gitops_repo_dir
            else:
                target_base = self.base_dir
                
            manifests_dir = os.path.join(target_base, "gitops", "manifests", self.service.name)
            
            for filename, content in manifests.items():
                self.write_file(manifests_dir, filename, content)
                
            # Also generate ArgoCD app (now uses correct path inside)
            self._generate_argocd_app(self.get_context())
            
        except Exception as e:
            print(f"   ❌ Manifest generation failed: {e}")
            return False
        
        # Step 4: Build image
        print("\nStep 4/6: Building Docker image...")
        if not self.build_image():
            return False
        
        # Step 5: Import to k3d
        print("\nStep 5/6: Importing to k3d...")
        self.import_to_k3d()
        
        # Step 6: Deploy & Push
        print("\nStep 6/6: Deploying & Pushing...")
        
        # Push to git FIRST so ArgoCD can sync
        if os.path.exists(self.gitops_repo_dir):
            if not self._push_to_git():
                print("   ⚠️  Git push failed, but continuing with local apply...")
        
        if not self.deploy():
            return False
        
        print(f"\n{'='*60}")
        print(f"✅ Service {self.service.name} created successfully!")
        print(f"{'='*60}")
        
        return True
