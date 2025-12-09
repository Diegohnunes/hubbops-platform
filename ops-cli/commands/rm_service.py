"""
Remove Service Command

Handles complete service removal including:
- ArgoCD Application deletion
- Kubernetes resources cleanup
- GitOps repository cleanup (persistent)
- Namespace deletion
"""

import os
import subprocess
import shutil

def run_command(cmd, cwd=None, check=True, env=None):
    """Execute shell command"""
    print(f"   Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, check=False, env=env)
    if result.returncode != 0:
        if check:
            print(f"   Error: {result.stderr}")
            raise Exception(f"Command failed: {cmd}")
        else:
            print(f"   Command failed (ignoring): {result.stderr.strip()}")
    return result.stdout


def rm_service_command(name, coin=None, service_type=None):
    """
    Remove a service completely.
    
    For new-style services (created via python-service/go-service templates):
    - name: service name (e.g., 'app-python')
    - coin/service_type: ignored (legacy args)
    
    The namespace defaults to the service name (isolation model).
    """
    print(f"\n{'='*60}")
    print(f"HubbOps: Removing service '{name}'")
    print(f"{'='*60}\n")

    base_dir = os.getcwd()
    gitops_repo_dir = os.environ.get("HUBBOPS_GITOPS_DIR", "/data/hubbops-infra")
    namespace = name  # Each service has its own namespace
    
    # SSH key for git operations
    ssh_key_path = "/data/ssh/id_rsa"
    git_env = os.environ.copy()
    if os.path.exists(ssh_key_path):
        git_env["GIT_SSH_COMMAND"] = f"ssh -i {ssh_key_path} -o StrictHostKeyChecking=no"
        print(f"   Using SSH key: {ssh_key_path}")

    # Step 1: Suspend ArgoCD Sync
    print("Step 1/7: Suspending ArgoCD auto-sync...")
    run_command(f"kubectl patch application {name} -n argocd --type=merge -p '{{\"spec\":{{\"syncPolicy\":null}}}}'", check=False)
    print(f"   ArgoCD auto-sync suspended")

    # Step 2: Ensure GitOps Repo is available
    print(f"\nStep 2/7: Preparing GitOps repository...")
    if os.path.exists(gitops_repo_dir):
        print(f"   Pulling latest changes...")
        run_command("git pull", cwd=gitops_repo_dir, check=False, env=git_env)
    else:
        print(f"   GitOps repo not found at {gitops_repo_dir}, will try local paths")

    # Step 3: Delete Files from GitOps Repo
    print(f"\nStep 3/7: Removing files from GitOps repository...")
    
    files_deleted = False
    
    # Try persistent repo first
    if os.path.exists(gitops_repo_dir):
        target_base = gitops_repo_dir
    else:
        target_base = base_dir  # Fallback to local
        
    argocd_file = os.path.join(target_base, "gitops", "apps", f"{name}.yaml")
    if os.path.exists(argocd_file):
        os.remove(argocd_file)
        print(f"   Deleted: gitops/apps/{name}.yaml")
        files_deleted = True
    
    manifests_dir = os.path.join(target_base, "gitops", "manifests", name)
    if os.path.exists(manifests_dir):
        shutil.rmtree(manifests_dir)
        print(f"   Deleted: gitops/manifests/{name}/")
        files_deleted = True
        
    # Also delete app code (local only)
    app_dir = os.path.join(base_dir, "apps", name)
    if os.path.exists(app_dir):
        shutil.rmtree(app_dir)
        print(f"   Deleted: apps/{name}/")

    # Step 4: Commit and Push to Git
    print(f"\nStep 4/7: Committing removal to Git...")
    if files_deleted and os.path.exists(gitops_repo_dir):
        try:
            run_command("git config user.name 'HubbOps Bot'", cwd=gitops_repo_dir, check=False)
            run_command("git config user.email 'bot@hubbops.io'", cwd=gitops_repo_dir, check=False)
            run_command("git add .", cwd=gitops_repo_dir, env=git_env)
            run_command(f'git commit -m "Remove service {name}"', cwd=gitops_repo_dir, check=False, env=git_env)
            run_command("git push", cwd=gitops_repo_dir, env=git_env)
            print(f"   ✅ Changes pushed to Git")
        except Exception as e:
            print(f"   ⚠️  Git push failed: {e}")
    else:
        print(f"   No files to commit or repo not available")

    # Step 5: Delete ArgoCD Application
    print("\nStep 5/7: Deleting ArgoCD application...")
    run_command(f"kubectl delete application -n argocd {name} --wait=false", check=False)
    print(f"   ArgoCD application deletion triggered")

    # Step 6: Delete Kubernetes Resources
    print(f"\nStep 6/7: Deleting Kubernetes resources...")
    run_command(f"kubectl delete deployment {name} -n {namespace} --wait=false", check=False)
    run_command(f"kubectl delete service {name} -n {namespace} --wait=false", check=False)
    run_command(f"kubectl delete configmap {name}-config -n {namespace} --wait=false", check=False)
    print(f"   Kubernetes resources deletion triggered")

    # Step 7: Delete Namespace
    print(f"\nStep 7/7: Deleting namespace {namespace}...")
    run_command(f"kubectl delete namespace {namespace} --wait=false", check=False)
    print(f"   Namespace deletion triggered")

    print(f"\n{'='*60}")
    print(f"✅ Service {name} removal complete!")
    print(f"{'='*60}")
    print(f"\nWhat was removed:")
    print(f"   • ArgoCD Application: {name}")
    print(f"   • Kubernetes Namespace: {namespace}")
    print(f"   • GitOps Files: gitops/manifests/{name}/, gitops/apps/{name}.yaml")
    print(f"   • Application Code: apps/{name}/")
    print(f"\nArgoCD prune will clean up any remaining resources.")
    print("")
