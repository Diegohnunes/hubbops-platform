import os
import subprocess
import time
from jinja2 import Environment, FileSystemLoader
import requests
import json
from config import get_config

def ensure_grafana_token(project_root):
    """Ensure a valid Grafana service account token exists for Terraform"""
    print(f"\nStep 10a/10: Verifying Grafana authorization...")
    
    tfvars_path = os.path.join(project_root, "terraform", "grafana", "terraform.tfvars")
    token = None
    
    # Get Grafana URL from env or default to localhost
    grafana_url = os.getenv("GRAFANA_URL", "http://localhost:3000")
    
    # 1. Check existing token
    if os.path.exists(tfvars_path):
        try:
            with open(tfvars_path, 'r') as f:
                for line in f:
                    if "grafana_service_account_token" in line:
                        token = line.split('=')[1].strip().strip('"')
                        break
        except Exception as e:
            print(f"   ⚠️  Error reading tfvars: {e}")

    # 2. Validate token if exists
    if token:
        try:
            # Check if Grafana is accessible first
            try:
                # Use /api/serviceaccounts/search to validate (requires Admin role which token has)
                response = requests.get(f"{grafana_url}/api/serviceaccounts/search", 
                                     headers={"Authorization": f"Bearer {token}"},
                                     timeout=2)
                if response.status_code == 200:
                    print("   ✅ Existing token is valid")
                    return True
                else:
                    print(f"   ⚠️  Existing token invalid (Status: {response.status_code})")
            except requests.exceptions.ConnectionError:
                print(f"   ⚠️  Grafana not accessible on {grafana_url}")
                print("   ℹ️  Cannot validate existing token.")
            except Exception as e:
                print(f"   ⚠️  Token validation failed: {e}")
        except Exception as e:
            print(f"   ⚠️  Token validation failed: {e}")

    # 3. Create new token if needed
    print("   🔄 Generating new Grafana token...")
    try:
        # Get admin credentials
        user_cmd = "kubectl get secret -n monitoring grafana-admin -o jsonpath='{.data.admin-user}' | base64 -d"
        pass_cmd = "kubectl get secret -n monitoring grafana-admin -o jsonpath='{.data.admin-password}' | base64 -d"
        
        admin_user = subprocess.run(user_cmd, shell=True, capture_output=True, text=True).stdout.strip()
        admin_pass = subprocess.run(pass_cmd, shell=True, capture_output=True, text=True).stdout.strip()
        
        if not admin_user or not admin_pass:
            print("   ❌ Could not retrieve Grafana admin credentials")
            return False

        # Create Service Account (idempotent)
        sa_payload = '{"name":"terraform-provisioner", "role":"Admin"}'
        create_sa_cmd = f"curl -s -X POST -H 'Content-Type: application/json' -u {admin_user}:{admin_pass} {grafana_url}/api/serviceaccounts -d '{sa_payload}'"
        subprocess.run(create_sa_cmd, shell=True, capture_output=True)

        # Get Service Account ID
        get_sa_cmd = f"curl -s -u {admin_user}:{admin_pass} {grafana_url}/api/serviceaccounts/search"
        sa_list = subprocess.run(get_sa_cmd, shell=True, capture_output=True, text=True).stdout
        
        sas_response = json.loads(sa_list)
        sas = sas_response.get('serviceAccounts', [])
        sa_id = next((sa['id'] for sa in sas if sa['name'] == 'terraform-provisioner'), None)
        
        if not sa_id:
            print("   ❌ Could not find terraform-provisioner service account")
            return False

        # Create Token
        token_payload = '{"name":"terraform-token-' + str(int(time.time())) + '"}'
        create_token_cmd = f"curl -s -X POST -H 'Content-Type: application/json' -u {admin_user}:{admin_pass} {grafana_url}/api/serviceaccounts/{sa_id}/tokens -d '{token_payload}'"
        token_resp = subprocess.run(create_token_cmd, shell=True, capture_output=True, text=True).stdout
        
        new_token = json.loads(token_resp).get('key')
        
        if new_token:
            # Save to tfvars
            os.makedirs(os.path.dirname(tfvars_path), exist_ok=True)
            with open(tfvars_path, 'w') as f:
                f.write(f'grafana_service_account_token = "{new_token}"\n')
                f.write(f'grafana_url = "{grafana_url}"\n')
            print("   ✅ New token generated and saved")
            return True
            
    except Exception as e:
        print(f"   ❌ Token generation failed: {e}")
        return False

    return False

def run_command(cmd, cwd=None, check=True):
    """Execute shell command and return output"""
    print(f"   Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print(f"   Error Output:\n{result.stderr}")
        if check:
            raise Exception(f"Command failed: {cmd}")
    return result.stdout

def create_service_command(name, coin, service_type):
    print(f"\n{'='*60}")
    print(f"IDP: Creating {name} ({service_type}) for {coin}")
    print(f"{'='*60}\n")

    # Load configuration
    cfg = get_config()
    
    # Validate config
    issues = cfg.validate()
    for issue in issues:
        print(f"⚠️  {issue}")

    # Paths
    base_dir = os.getcwd()
    templates_dir = os.path.join(base_dir, "ops-cli", "templates")
    output_manifests_dir = os.path.join(base_dir, "gitops", "manifests", name)
    output_apps_dir = os.path.join(base_dir, "gitops", "apps")
    output_code_dir = os.path.join(base_dir, "apps", name)
    namespace = cfg.default_namespace

    # Image name from config
    image_name = cfg.get_image_name(name, "v2.0")

    # Context for templates
    context = {
        "name": name,
        "coin": coin.upper(),
        "type": service_type,
        "image": image_name,
        "namespace": namespace
    }

    # Jinja2 Setup
    env = Environment(loader=FileSystemLoader(templates_dir))


    print("Step 1/10: Generating application code...")
    os.makedirs(output_code_dir, exist_ok=True)
    generate_file(env, "main.go.j2", output_code_dir, "main.go", context)
    generate_file(env, "go.mod.j2", output_code_dir, "go.mod", context)
    

    dockerfile_src = os.path.join(templates_dir, "Dockerfile")
    dockerfile_dst = os.path.join(output_code_dir, "Dockerfile")
    with open(dockerfile_src, 'r') as src, open(dockerfile_dst, 'w') as dst:
        dst.write(src.read())
    print(f"   Created Dockerfile")



    print("\nStep 2/10: Building Docker image...")
    run_command(f"docker build -t {image_name} apps/{name}", cwd=base_dir)
    print(f"   Image built: {image_name}")


    print("\nStep 3/10: Importing image to k3d...")
    run_command(f"k3d image import {image_name} -c {cfg.k3d_cluster}", cwd=base_dir)
    print(f"   Image imported to k3d")


    print(f"\nStep 4/10: Skipping namespace/PV creation (using shared default namespace)...")
    print(f"   All services use shared crypto-shared-storage-v3 PVC in {namespace} namespace")


    print("\nStep 5/10: Generating Kubernetes manifests...")
    os.makedirs(output_manifests_dir, exist_ok=True)
    generate_file(env, "deployment.yaml.j2", output_manifests_dir, "deployment.yaml", context)
    generate_file(env, "service.yaml.j2", output_manifests_dir, "service.yaml", context)
    generate_file(env, "configmap.yaml.j2", output_manifests_dir, "configmap.yaml", context)


    print("\nStep 6/10: Generating ArgoCD application...")
    os.makedirs(output_apps_dir, exist_ok=True)
    generate_file(env, "argocd-app.yaml.j2", output_apps_dir, f"{name}.yaml", context)


    print("\nStep 7/10: Committing to Git (Multi-Repo)...")
    
    # Get Git repos from config
    git_apps = cfg.git_apps_repo
    git_infra = cfg.git_infra_repo
    
    if not git_apps and not git_infra:
        print("   ⚠️  Git repositories not configured. Skipping Git push.")
        print("   ℹ️  Configure git.repositories in config/settings.yaml")
        print("   ℹ️  Files generated locally only.")
    else:
        import shutil
        
        # Helper to handle git operations for a specific repo
        def push_to_repo(repo_url, source_dir, target_subpath, commit_msg):
            if not repo_url:
                return False
            repo_name = repo_url.split('/')[-1].replace('.git', '')
            temp_dir = os.path.join("/tmp", f"repo_{repo_name}_{int(time.time())}")
            
            print(f"   🔄 Processing {repo_name}...")
            try:
                # Clone
                run_command(f"git clone {repo_url} {temp_dir}", check=False)
                
                # If clone failed (repo might be empty/new), try init
                if not os.path.exists(os.path.join(temp_dir, ".git")):
                    os.makedirs(temp_dir, exist_ok=True)
                    run_command("git init", cwd=temp_dir)
                    run_command(f"git remote add origin {repo_url}", cwd=temp_dir)
                    run_command("git checkout -b main", cwd=temp_dir, check=False)

                # Copy files
                dest_path = os.path.join(temp_dir, target_subpath)
                os.makedirs(dest_path, exist_ok=True)
                
                # Copy recursively
                if os.path.exists(source_dir):
                    for item in os.listdir(source_dir):
                        s = os.path.join(source_dir, item)
                        d = os.path.join(dest_path, item)
                        if os.path.isdir(s):
                            shutil.copytree(s, d, dirs_exist_ok=True)
                        else:
                            shutil.copy2(s, d)
                
                # Commit and Push
                run_command("git add .", cwd=temp_dir)
                run_command(f'git commit -m "{commit_msg}"', cwd=temp_dir, check=False)
                run_command("git pull --rebase origin main", cwd=temp_dir, check=False)
                run_command("git push origin main", cwd=temp_dir)
                print(f"   ✅ Pushed to {repo_name}")
                
                # Cleanup
                shutil.rmtree(temp_dir)
                return True
            except Exception as e:
                print(f"   ❌ Failed to push to {repo_name}: {e}")
                return False

        # 1. Push Application Code to Apps Repo
        if git_apps:
            push_to_repo(git_apps, output_code_dir, f"apps/{name}", f"feat: add {name} service")

        # 2. Push Manifests to Infra Repo
        if git_infra:
            infra_temp_dir = os.path.join("/tmp", f"repo_infra_{int(time.time())}")
            
            print(f"   🔄 Processing infra repository...")
            run_command(f"git clone {git_infra} {infra_temp_dir}", check=False)
            if not os.path.exists(os.path.join(infra_temp_dir, ".git")):
                os.makedirs(infra_temp_dir, exist_ok=True)
                run_command("git init", cwd=infra_temp_dir)
                run_command(f"git remote add origin {git_infra}", cwd=infra_temp_dir)
                run_command("git checkout -b main", cwd=infra_temp_dir, check=False)

            # Copy Manifests
            manifest_dest = os.path.join(infra_temp_dir, "gitops", "manifests", name)
            os.makedirs(manifest_dest, exist_ok=True)
            for item in os.listdir(output_manifests_dir):
                s = os.path.join(output_manifests_dir, item)
                d = os.path.join(manifest_dest, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)
            
            # Copy ArgoCD App
            app_dest = os.path.join(infra_temp_dir, "gitops", "apps")
            os.makedirs(app_dest, exist_ok=True)
            shutil.copy2(os.path.join(output_apps_dir, f"{name}.yaml"), app_dest)
            
            # Push Infra
            run_command("git add .", cwd=infra_temp_dir)
            run_command(f'git commit -m "feat: add {name} manifests"', cwd=infra_temp_dir, check=False)
            run_command("git pull --rebase origin main", cwd=infra_temp_dir, check=False)
            run_command("git push origin main", cwd=infra_temp_dir)
            print(f"   ✅ Pushed to infra repository")
            
            shutil.rmtree(infra_temp_dir)

        print(f"   Changes pushed to Git repositories")

    print("\nStep 8/10: Deploying to Kubernetes via ArgoCD...")
    # We need to apply the ArgoCD app from the INFRA repo (or local file is fine for initial apply)
    run_command(f"kubectl apply -f gitops/apps/{name}.yaml", cwd=base_dir)
    time.sleep(5) # Wait a bit for ArgoCD to detect the app
    run_command(f"kubectl -n argocd annotate application {name} argocd.argoproj.io/refresh=hard --overwrite", cwd=base_dir)
    print(f"   ArgoCD application deployed")


    print(f"\nStep 9/10: Waiting for pod to be ready...")
    print(f"   Timeout: 120 seconds")
    try:
        # First wait for deployment to be created by ArgoCD
        print(f"   Waiting for deployment {name} to be created...")
        for _ in range(30):
            check_deploy = run_command(f"kubectl get deployment -n {namespace} {name}", check=False)
            if "NotFound" not in check_deploy and "not found" not in check_deploy and name in check_deploy:
                print(f"   Deployment created")
                break
            time.sleep(2)
        else:
            print(f"   Warning: Deployment not found after 60s")

        # Then wait for pod
        run_command(f"kubectl wait --for=condition=Ready pod -l app={name} -n {namespace} --timeout=120s", cwd=base_dir)
        print(f"   Pod is ready!")
        

        print(f"\nLatest logs:")
        logs = run_command(f"kubectl logs -n {namespace} -l app={name} --tail=10", cwd=base_dir, check=False)
        for line in logs.split('\n')[:10]:
            if line:
                print(f"   {line}")
    except:
        print(f"   Pod took longer than expected, but deployment is in progress")
        print(f"   Check status with: kubectl get pods -n {namespace}")




    # Step 10/10: Generate and apply Terraform dashboard
    print("\nStep 10/10: Creating Grafana dashboard with Terraform...")

    # Ensure valid token before proceeding
    if not ensure_grafana_token(base_dir):
        print("   ⚠️  Skipping dashboard creation (Authorization failed)")
    else:
        terraform_dir = os.path.join(base_dir, "terraform", "grafana")
        # os.makedirs(terraform_dir, exist_ok=True) - Not needed for root dir

        # Generate provider.tf (ensures correct Grafana provider)
        provider_tf_path = os.path.join(terraform_dir, "provider.tf")
        if not os.path.exists(provider_tf_path):
            generate_file(env, "provider.tf.j2", terraform_dir, "provider.tf", context)
            print(f"   Created provider.tf")

        # Generate Terraform file from template
        dashboard_tf_path = os.path.join(terraform_dir, f"{name}.tf")
        generate_file(env, "dashboard.tf.j2", terraform_dir, f"{name}.tf", context)

        # Apply Terraform
        print("   Initializing Terraform...")
        result = subprocess.run(
            ["terraform", "init"],
            cwd=os.path.join(base_dir, "terraform", "grafana"),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"   ❌ Terraform init failed: {result.stderr}")
            print(f"   ⚠️  Dashboard creation skipped.")
            print(f"   ℹ️  Service is operational")
            print(f"   ℹ️  Create dashboard manually later if needed")
        else:
            print("   Applying Terraform configuration...")
            # Resource name in template uses underscores (e.g. btc_collector_apm)
            # but name variable has hyphens (e.g. btc-collector)
            tf_resource_name = f"grafana_dashboard.{name.replace('-', '_')}_apm"
            
            result = subprocess.run(
                ["terraform", "apply", "-auto-approve", f"-target={tf_resource_name}"],
                cwd=os.path.join(base_dir, "terraform", "grafana"),
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                if "Connection refused" in result.stderr:
                     print(f"   ⚠️  Grafana not accessible on localhost:3000")
                     print(f"   ℹ️  Dashboard config created but not applied")
                     print(f"   ℹ️  Run manually: cd terraform/grafana && terraform apply")
                else:
                     print(f"   ⚠️  Dashboard creation skipped: {result.stderr.splitlines()[0] if result.stderr else 'Unknown error'}")
                     print(f"   ℹ️  Service is operational")
                     print(f"   ℹ️  Create dashboard manually later if needed")
            else:
                print(f"   ✅ Grafana dashboard created: {name}-apm")


    # Step 11/11: Restart frontend to ensure new data is visible
    print("\nStep 11/11: Restarting frontend to refresh cache...")
    run_command(f"kubectl rollout restart deployment/crypto-frontend -n {namespace}")
    print("   Frontend restarted (SQLite cache will be refreshed)")

    print(f"\n{'='*60}")
    print(f"IDP: Service {name} created successfully!")
    print(f"{'='*60}")
    print(f"\nSummary:")
    print(f"   • Application: {name}")
    print(f"   • Coin: {coin}")
    print(f"   • Namespace: {namespace}")
    print(f"   • Image: {image_name}")
    print(f"   • Code: apps/{name}/main.go")
    print(f"   • Manifests: gitops/manifests/{name}/")
    print(f"   • ArgoCD: gitops/apps/{name}.yaml")
    print(f"   • Dashboard: http://localhost:3000/d/{name}-apm")
    
    print(f"\nUseful commands:")
    print(f"   kubectl get pods -n {namespace}")
    print(f"   kubectl logs -n {namespace} -l app={name} -f")
    print(f"   curl http://localhost:4000/api/prices")
    
    print(f"\nTo remove:")
    print(f"   python ops-cli/main.py rm-service {name} {coin} {service_type}")
    print("")

def generate_file(env, template_name, output_dir, output_filename, context):
    template = env.get_template(template_name)
    content = template.render(context)
    output_path = os.path.join(output_dir, output_filename)
    
    with open(output_path, "w") as f:
        f.write(content)
    print(f"   Created {output_filename}")


