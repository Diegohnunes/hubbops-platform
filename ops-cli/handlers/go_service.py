"""
Go Service Handler

Creates Go applications with standard HTTP server and Kubernetes deployment.
"""

import os
from typing import Dict, Any
from .base import BaseHandler, ServiceConfig


class GoServiceHandler(BaseHandler):
    """Handler for go-service template"""
    
    template_id = "go-service"
    
    def get_template_subdir(self) -> str:
        return "go"
    
    def validate(self) -> tuple[bool, list[str]]:
        """Validate Go service configuration"""
        errors = []
        
        if not self.service.name:
            errors.append("service_name is required")
        
        name = self.service.name
        if not name.replace('-', '').replace('_', '').isalnum():
            errors.append("service_name must contain only alphanumeric characters, hyphens, and underscores")
        
        port = self.service.get("port", 8080)
        if not isinstance(port, int) or port < 1 or port > 65535:
            errors.append("port must be between 1 and 65535")
        
        return len(errors) == 0, errors
    
    def get_context(self) -> Dict[str, Any]:
        """Build template context from form config"""
        config = self.service.config
        
        return {
            "name": self.service.name,
            "namespace": self.service.namespace,
            "image": self.get_image_name(),
            "environment": config.get("environment", "dev"),
            "go_version": config.get("go_version", "1.21"),
            "port": config.get("port", 8080),
            "cpu_limit": config.get("cpu_limit", "250m"),
            "memory_limit": config.get("memory_limit", "256Mi"),
            "cpu_request": config.get("request_cpu", "100m"),
            "memory_request": config.get("request_memory", "128Mi"),
            "replicas": config.get("replicas", 2),
            "enable_pprof": config.get("enable_pprof", False),
            "enable_health_check": config.get("enable_health_check", True),
            "log_level": config.get("log_level", "INFO"),
        }
    
    def generate_code(self) -> str:
        """Generate Go application code"""
        output_dir = os.path.join(self.base_dir, "apps", self.service.name)
        os.makedirs(output_dir, exist_ok=True)
        
        context = self.get_context()
        
        # Generate main.go
        main_go = self._generate_main_go(context)
        self.write_file(output_dir, "main.go", main_go)
        
        # Generate go.mod
        go_mod = self._generate_go_mod(context)
        self.write_file(output_dir, "go.mod", go_mod)
        
        # Generate Dockerfile
        dockerfile = self._generate_dockerfile(context)
        self.write_file(output_dir, "Dockerfile", dockerfile)
        
        return output_dir
    
    def _generate_main_go(self, context: Dict[str, Any]) -> str:
        """Generate main.go"""
        name = context["name"]
        port = context.get("port", 8080)
        enable_pprof = context.get("enable_pprof", False)
        
        pprof_import = ""
        pprof_handler = ""
        if enable_pprof:
            pprof_import = '\n\t_ "net/http/pprof"'
            pprof_handler = '''
	// pprof is automatically registered on /debug/pprof/
	log.Println("pprof enabled at /debug/pprof/")'''
        
        return f'''package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
	"time"{pprof_import}
)

type Response struct {{
	Service string `json:"service"`
	Status  string `json:"status"`
	Time    string `json:"time,omitempty"`
}}

func main() {{
	log.SetFlags(log.LstdFlags | log.Lshortfile)
	log.Printf("Starting {name} service...")

	http.HandleFunc("/", handleRoot)
	http.HandleFunc("/health", handleHealth)
	http.HandleFunc("/ready", handleReady)
{pprof_handler}

	port := os.Getenv("PORT")
	if port == "" {{
		port = "{port}"
	}}

	log.Printf("Listening on :%s", port)
	if err := http.ListenAndServe(":"+port, nil); err != nil {{
		log.Fatalf("Server failed: %v", err)
	}}
}}

func handleRoot(w http.ResponseWriter, r *http.Request) {{
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(Response{{
		Service: "{name}",
		Status:  "running",
		Time:    time.Now().Format(time.RFC3339),
	}})
}}

func handleHealth(w http.ResponseWriter, r *http.Request) {{
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(Response{{
		Status: "healthy",
	}})
}}

func handleReady(w http.ResponseWriter, r *http.Request) {{
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(Response{{
		Status: "ready",
	}})
}}
'''
    
    def _generate_go_mod(self, context: Dict[str, Any]) -> str:
        """Generate go.mod"""
        name = context["name"]
        go_version = context.get("go_version", "1.21")
        
        return f'''module {name}

go {go_version}
'''
    
    def _generate_dockerfile(self, context: Dict[str, Any]) -> str:
        """Generate multi-stage Dockerfile"""
        go_version = context.get("go_version", "1.21")
        port = context.get("port", 8080)
        
        return f'''# Build stage
FROM golang:{go_version}-alpine AS builder

WORKDIR /app
COPY go.mod ./
# RUN go mod download  # Uncomment if you have dependencies
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o main .

# Runtime stage
FROM alpine:3.19

RUN apk --no-cache add ca-certificates
WORKDIR /root/

COPY --from=builder /app/main .

EXPOSE {port}
CMD ["./main"]
'''
    
    def generate_manifests(self) -> Dict[str, str]:
        """Generate Kubernetes manifests"""
        context = self.get_context()
        manifests = {}
        
        # Namespace (for service isolation)
        manifests["namespace.yaml"] = self._generate_namespace_yaml(context)
        
        manifests["deployment.yaml"] = self._generate_deployment(context)
        manifests["service.yaml"] = self._generate_service(context)
        
        # Generate ArgoCD app (uses base class method)
        self._generate_argocd_app(context)
        
        return manifests
    
    def _generate_deployment(self, context: Dict[str, Any]) -> str:
        """Generate Kubernetes Deployment"""
        name = context["name"]
        namespace = context["namespace"]
        image = context["image"]
        port = context.get("port", 8080)
        replicas = context.get("replicas", 2)
        cpu_limit = context.get("cpu_limit", "250m")
        memory_limit = context.get("memory_limit", "256Mi")
        cpu_request = context.get("cpu_request", "100m")
        memory_request = context.get("memory_request", "128Mi")
        
        probes = ""
        if context.get("enable_health_check", True):
            probes = f'''
          livenessProbe:
            httpGet:
              path: /health
              port: {port}
            initialDelaySeconds: 5
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /ready
              port: {port}
            initialDelaySeconds: 3
            periodSeconds: 10'''
        
        return f'''apiVersion: apps/v1
kind: Deployment
metadata:
  name: {name}
  namespace: {namespace}
  labels:
    app: {name}
spec:
  replicas: {replicas}
  selector:
    matchLabels:
      app: {name}
  template:
    metadata:
      labels:
        app: {name}
    spec:
      containers:
      - name: {name}
        image: {image}
        ports:
        - containerPort: {port}
        resources:
          limits:
            cpu: {cpu_limit}
            memory: {memory_limit}
          requests:
            cpu: {cpu_request}
            memory: {memory_request}
        env:
        - name: PORT
          value: "{port}"{probes}
'''
    
    def _generate_service(self, context: Dict[str, Any]) -> str:
        """Generate Kubernetes Service"""
        name = context["name"]
        namespace = context["namespace"]
        port = context.get("port", 8080)
        
        return f'''apiVersion: v1
kind: Service
metadata:
  name: {name}
  namespace: {namespace}
  labels:
    app: {name}
spec:
  selector:
    app: {name}
  ports:
  - port: {port}
    targetPort: {port}
    protocol: TCP
'''

