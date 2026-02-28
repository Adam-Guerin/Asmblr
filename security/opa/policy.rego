# Open Policy Agent (OPA) Policy for Asmblr
# Enforces security policies and compliance requirements

package asmblr.security

# Default deny all
default allow = false

# Allow if all checks pass
allow {
    input.method == "create"
    check_pod_security()
    check_resource_limits()
    check_image_security()
    check_network_policy()
}

# Pod security checks
check_pod_security {
    not input.spec.securityContext.privileged
    not input.spec.securityContext.runAsRoot
    input.spec.securityContext.runAsNonRoot == true
    input.spec.securityContext.readOnlyRootFilesystem == true
    input.spec.securityContext.allowPrivilegeEscalation == false
    input.spec.securityContext.capabilities.drop[_] == "ALL"
}

# Resource limits checks
check_resource_limits {
    input.spec.resources.limits.cpu
    input.spec.resources.limits.memory
    input.spec.resources.requests.cpu
    input.spec.resources.requests.memory
}

# Image security checks
check_image_security {
    not contains(input.spec.image, ":latest")
    contains(input.spec.image, "asmblr/")
    not contains(input.spec.image, "library/")
}

# Network policy checks
check_network_policy {
    input.spec.hostNetwork == false
    input.spec.hostPID == false
    input.spec.hostIPC == false
}

# RBAC policies
package asmblr.rbac

# Service account permissions
deny_service_account_privileged {
    input.kind == "ServiceAccount"
    input.metadata.name == "default"
}

# Role binding checks
allow_role_binding {
    input.kind == "RoleBinding"
    input.roleRef.name != "cluster-admin"
    input.roleRef.name != "admin"
    input.subjects[_].kind == "ServiceAccount"
}

# Network policies
package asmblr.network

# Deny all ingress by default
deny_all_ingress {
    input.kind == "NetworkPolicy"
    input.spec.policyTypes[_] == "Ingress"
    not input.spec.ingress
}

# Allow only specific ports
allow_specific_ports {
    input.kind == "NetworkPolicy"
    input.spec.ingress[_].ports[_].port in [80, 443, 8000, 8501, 6379, 11434, 9090, 3001]
}

# Compliance policies
package asmblr.compliance

# GDPR compliance
deny_gdpr_violation {
    input.kind == "Secret"
    contains(input.metadata.name, "personal")
    contains(input.metadata.name, "pii")
}

# SOC2 compliance
deny_soc2_violation {
    input.kind == "ConfigMap"
    contains(input.data[_], "password")
    contains(input.data[_], "secret")
    contains(input.data[_], "key")
}

# PCI-DSS compliance
deny_pci_violation {
    input.kind == "PersistentVolume"
    input.spec.accessModes[_] == "ReadWriteOnce"
    not input.spec.storageClassName
}

# Resource quotas
package asmblr.quota

# CPU quota check
deny_cpu_quota_exceeded {
    input.kind == "Pod"
    sum_cpu_requests > cpu_quota_limit
}

sum_cpu_requests = sum { request |
    input.spec.containers[_].resources.requests.cpu == request
}

cpu_quota_limit = 10000  # 10 cores

# Memory quota check
deny_memory_quota_exceeded {
    input.kind == "Pod"
    sum_memory_requests > memory_quota_limit
}

sum_memory_requests = sum { request |
    input.spec.containers[_].resources.requests.memory == request
}

memory_quota_limit = "32Gi"

# Image security policies
package asmblr.image

# Allow only trusted registries
allow_trusted_registry {
    contains(input.spec.image, "docker.io/asmblr/")
    or contains(input.spec.image, "gcr.io/asmblr/")
    or contains(input.spec.image, "quay.io/asmblr/")
}

# Deny images with vulnerabilities
deny_vulnerable_images {
    input.kind == "Pod"
    input.spec.containers[_].image in vulnerable_images
}

vulnerable_images = [
    "docker.io/library/ubuntu:18.04",
    "docker.io/library/centos:7",
    "docker.io/library/alpine:3.8"
]

# Pod security standards
package asmblr.pod_security

# Enforce Pod Security Standards
deny_privileged_pod {
    input.kind == "Pod"
    input.spec.containers[_].securityContext.privileged == true
}

deny_host_network {
    input.kind == "Pod"
    input.spec.hostNetwork == true
}

deny_host_pid {
    input.kind == "Pod"
    input.spec.hostPID == true
}

deny_host_ipc {
    input.kind == "Pod"
    input.spec.hostIPC == true
}

# Container security
package asmblr.container

# Deny containers running as root
deny_root_container {
    input.kind == "Pod"
    input.spec.containers[_].securityContext.runAsUser == 0
}

# Deny containers with dangerous capabilities
deny_dangerous_capabilities {
    input.kind == "Pod"
    input.spec.containers[_].securityContext.capabilities.add[_] in dangerous_caps
}

dangerous_caps = [
    "CAP_SYS_ADMIN",
    "CAP_NET_ADMIN",
    "CAP_SYS_PTRACE",
    "CAP_SYS_MODULE",
    "CAP_DAC_READ_SEARCH"
]

# Storage policies
package asmblr.storage

# Deny host path volumes
deny_host_path_volumes {
    input.kind == "Pod"
    input.spec.volumes[_].hostPath
}

# Allow only specific storage classes
allow_storage_class {
    input.kind == "PersistentVolumeClaim"
    input.spec.storageClassName in allowed_storage_classes
}

allowed_storage_classes = [
    "gp2",
    "gp3",
    "standard",
    "premium-ssd"
]

# Admission control policies
package asmblr.admission

# Validate labels
deny_missing_labels {
    input.kind == "Pod"
    not has_required_labels
}

has_required_labels {
    input.metadata.labels["app.kubernetes.io/name"]
    input.metadata.labels["app.kubernetes.io/instance"]
    input.metadata.labels["app.kubernetes.io/version"]
}

# Validate annotations
deny_missing_annotations {
    input.kind == "Deployment"
    not has_required_annotations
}

has_required_annotations {
    input.metadata.annotations["kubectl.kubernetes.io/restartedAt"]
    input.metadata.annotations["deployment.kubernetes.io/revision"]
}

# Namespace policies
package asmblr.namespace

# Restrict namespace creation
deny_unauthorized_namespace {
    input.kind == "Namespace"
    not input.metadata.name in allowed_namespaces
}

allowed_namespaces = [
    "default",
    "kube-system",
    "kube-public",
    "kube-node-lease",
    "asmblr-dev",
    "asmblr-staging",
    "asmblr-production"
]

# Monitoring policies
package asmblr.monitoring

# Require monitoring labels
deny_missing_monitoring_labels {
    input.kind == "Deployment"
    not input.metadata.labels["monitoring.enabled"] == "true"
}

# Require prometheus annotations
deny_missing_prometheus_annotations {
    input.kind == "Service"
    not input.metadata.annotations["prometheus.io/scrape"]
    not input.metadata.annotations["prometheus.io/port"]
}

# Secret management
package asmblr.secrets

# Deny secrets in ConfigMaps
deny_secrets_in_configmap {
    input.kind == "ConfigMap"
    sensitive_data_in_configmap
}

sensitive_data_in_configmap {
    data := input.data[_]
    contains(data, "password") or
    contains(data, "secret") or
    contains(data, "key") or
    contains(data, "token")
}

# Require secret encryption
deny_unencrypted_secrets {
    input.kind == "Secret"
    not input.metadata.annotations["kubernetes.io/encryption-config"]
}

# Audit policies
package asmblr.audit

# Log all security events
audit_security_events {
    input.kind == "Pod"
    security_violation
}

security_violation {
    input.spec.containers[_].securityContext.privileged == true
    or input.spec.hostNetwork == true
    or input.spec.hostPID == true
    or input.spec.hostIPC == true
}
