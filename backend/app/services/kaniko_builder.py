"""
Kaniko Builder Service

Builds container images inside Kubernetes using Kaniko.
This eliminates the need for Docker daemon access inside the cluster.
"""

import asyncio
import logging
import os
import uuid
from datetime import datetime
from typing import AsyncGenerator, Optional, Tuple

from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)


class KanikoBuilder:
    """
    Builds Docker images using Kaniko Jobs in Kubernetes.
    
    Kaniko runs as a Kubernetes Job that:
    1. Reads build context from a PVC
    2. Builds the image
    3. Pushes to a registry
    """
    
    KANIKO_IMAGE = "gcr.io/kaniko-project/executor:latest"
    BUILD_NAMESPACE = "hubbops"
    BUILD_CONTEXT_PVC = "hubbops-backend-data"
    
    def __init__(self):
        """Initialize Kubernetes client"""
        try:
            # Try in-cluster config first (when running inside K8s)
            config.load_incluster_config()
        except config.ConfigException:
            # Fall back to kubeconfig (local development)
            config.load_kube_config()
        
        self.batch_v1 = client.BatchV1Api()
        self.core_v1 = client.CoreV1Api()
        
        # Registry configuration
        self.registry = os.environ.get("KANIKO_REGISTRY", "k3d-devlab-registry:5000")
        self.insecure_registry = os.environ.get("KANIKO_INSECURE", "true").lower() == "true"
    
    def get_image_destination(self, service_name: str, tag: str = "v1.0") -> str:
        """Get the full image destination for Kaniko to push to"""
        return f"{self.registry}/{service_name}:{tag}"
    
    async def build_and_push(
        self, 
        service_name: str, 
        context_path: str,
        destination: Optional[str] = None,
        dockerfile: str = "Dockerfile"
    ) -> Tuple[bool, str]:
        """
        Build and push an image using Kaniko.
        
        Args:
            service_name: Name of the service being built
            context_path: Path to the build context (relative to PVC mount)
            destination: Full image destination (registry/name:tag)
            dockerfile: Name of the Dockerfile
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not destination:
            destination = self.get_image_destination(service_name)
        
        job_name = f"kaniko-{service_name}-{uuid.uuid4().hex[:8]}"
        
        logger.info(f"Starting Kaniko build job: {job_name}")
        logger.info(f"  Context: {context_path}")
        logger.info(f"  Destination: {destination}")
        
        try:
            # Create the Kaniko job
            job = self._create_job_manifest(
                job_name=job_name,
                context_path=context_path,
                destination=destination,
                dockerfile=dockerfile
            )
            
            # Submit the job
            self.batch_v1.create_namespaced_job(
                namespace=self.BUILD_NAMESPACE,
                body=job
            )
            
            logger.info(f"Kaniko job created: {job_name}")
            
            # Wait for completion and stream logs
            success = await self._wait_for_job(job_name)
            
            if success:
                return True, f"Image built and pushed: {destination}"
            else:
                return False, f"Build failed. Check logs for job: {job_name}"
                
        except ApiException as e:
            logger.error(f"Kubernetes API error: {e}")
            return False, f"Failed to create build job: {e.reason}"
        except Exception as e:
            logger.error(f"Build error: {e}")
            return False, str(e)
    
    def _create_job_manifest(
        self,
        job_name: str,
        context_path: str,
        destination: str,
        dockerfile: str
    ) -> client.V1Job:
        """Create the Kubernetes Job manifest for Kaniko"""
        
        # Kaniko arguments
        args = [
            f"--context=dir:///workspace/{context_path}",
            f"--dockerfile=/workspace/{context_path}/{dockerfile}",
            f"--destination={destination}",
            "--cache=true",
            "--cache-ttl=24h",
        ]
        
        # Add insecure registry flag for local dev
        if self.insecure_registry:
            args.append("--insecure")
            args.append(f"--insecure-registry={self.registry}")
        
        # Container spec
        container = client.V1Container(
            name="kaniko",
            image=self.KANIKO_IMAGE,
            args=args,
            volume_mounts=[
                client.V1VolumeMount(
                    name="build-context",
                    mount_path="/workspace"
                )
            ],
            resources=client.V1ResourceRequirements(
                requests={"memory": "512Mi", "cpu": "250m"},
                limits={"memory": "2Gi", "cpu": "1"}
            )
        )
        
        # Pod spec
        pod_spec = client.V1PodSpec(
            containers=[container],
            restart_policy="Never",
            service_account_name="kaniko-builder",
            volumes=[
                client.V1Volume(
                    name="build-context",
                    persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                        claim_name=self.BUILD_CONTEXT_PVC
                    )
                )
            ]
        )
        
        # Job spec
        job_spec = client.V1JobSpec(
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(
                    labels={"app": "kaniko", "service": job_name}
                ),
                spec=pod_spec
            ),
            backoff_limit=0,  # Don't retry on failure
            ttl_seconds_after_finished=300  # Clean up after 5 minutes
        )
        
        # Job
        job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(
                name=job_name,
                namespace=self.BUILD_NAMESPACE,
                labels={"app": "kaniko", "managed-by": "hubbops"}
            ),
            spec=job_spec
        )
        
        return job
    
    async def _wait_for_job(self, job_name: str, timeout: int = 600) -> bool:
        """
        Wait for a Kaniko job to complete.
        
        Args:
            job_name: Name of the job
            timeout: Maximum seconds to wait
            
        Returns:
            True if job succeeded, False otherwise
        """
        start_time = datetime.now()
        pod_name = None
        
        while (datetime.now() - start_time).seconds < timeout:
            try:
                # Get job status
                job = self.batch_v1.read_namespaced_job_status(
                    name=job_name,
                    namespace=self.BUILD_NAMESPACE
                )
                
                # Check if completed
                if job.status.succeeded:
                    logger.info(f"Kaniko job {job_name} succeeded")
                    return True
                
                if job.status.failed:
                    logger.error(f"Kaniko job {job_name} failed")
                    return False
                
                # Get pod name for logging
                if not pod_name:
                    pods = self.core_v1.list_namespaced_pod(
                        namespace=self.BUILD_NAMESPACE,
                        label_selector=f"job-name={job_name}"
                    )
                    if pods.items:
                        pod_name = pods.items[0].metadata.name
                
            except ApiException as e:
                logger.warning(f"Error checking job status: {e}")
            
            await asyncio.sleep(2)
        
        logger.error(f"Kaniko job {job_name} timed out after {timeout}s")
        return False
    
    async def stream_build_logs(self, job_name: str) -> AsyncGenerator[str, None]:
        """
        Stream logs from a Kaniko build job.
        
        Args:
            job_name: Name of the Kaniko job
            
        Yields:
            Log lines from the build
        """
        # Wait for pod to be created
        pod_name = None
        for _ in range(30):  # Wait up to 30 seconds for pod
            try:
                pods = self.core_v1.list_namespaced_pod(
                    namespace=self.BUILD_NAMESPACE,
                    label_selector=f"job-name={job_name}"
                )
                if pods.items:
                    pod_name = pods.items[0].metadata.name
                    break
            except ApiException:
                pass
            await asyncio.sleep(1)
        
        if not pod_name:
            yield "ERROR: Could not find Kaniko pod"
            return
        
        # Wait for pod to start running
        for _ in range(60):
            try:
                pod = self.core_v1.read_namespaced_pod(
                    name=pod_name,
                    namespace=self.BUILD_NAMESPACE
                )
                if pod.status.phase in ["Running", "Succeeded", "Failed"]:
                    break
            except ApiException:
                pass
            await asyncio.sleep(1)
        
        # Stream logs
        try:
            # Use follow=True for streaming
            log_stream = self.core_v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=self.BUILD_NAMESPACE,
                follow=True,
                _preload_content=False
            )
            
            for line in log_stream:
                if isinstance(line, bytes):
                    line = line.decode('utf-8')
                yield line.strip()
                
        except ApiException as e:
            yield f"ERROR: Failed to stream logs: {e.reason}"
    
    async def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Clean up old Kaniko jobs"""
        try:
            jobs = self.batch_v1.list_namespaced_job(
                namespace=self.BUILD_NAMESPACE,
                label_selector="app=kaniko"
            )
            
            now = datetime.now()
            for job in jobs.items:
                if job.status.completion_time:
                    age = now - job.status.completion_time.replace(tzinfo=None)
                    if age.total_seconds() > max_age_hours * 3600:
                        self.batch_v1.delete_namespaced_job(
                            name=job.metadata.name,
                            namespace=self.BUILD_NAMESPACE,
                            propagation_policy="Background"
                        )
                        logger.info(f"Cleaned up old job: {job.metadata.name}")
                        
        except ApiException as e:
            logger.warning(f"Error cleaning up jobs: {e}")
