"""
Clustering Quality metric - Adjusted Rand Index vs ground truth clusters.
"""

from typing import Dict, List, Any, Set, Tuple
import numpy as np
from collections import defaultdict

from .base import BaseMetric, MetricResult


class ClusteringQuality(BaseMetric):
    """Measures clustering quality using Adjusted Rand Index."""
    
    requires_ground_truth = True
    output_type = "score"
    
    def compute(self, run_result: Dict[str, Any], dataset: List[Dict]) -> MetricResult:
        """Compute clustering quality metrics."""
        # Extract system clusters
        system_clusters = self._extract_system_clusters(run_result)
        if not system_clusters:
            return MetricResult(
                score=0.0,
                explanation="No clusters extracted by system",
                evidence={"system_clusters_count": 0}
            )
        
        # Get ground truth clusters
        ground_truth_clusters = self._extract_ground_truth_clusters(dataset)
        
        # Calculate clustering metrics
        ari = self._calculate_adjusted_rand_index(system_clusters, ground_truth_clusters)
        purity = self._calculate_purity(system_clusters, ground_truth_clusters)
        nmi = self._calculate_normalized_mutual_info(system_clusters, ground_truth_clusters)
        
        # Combined score (weighted towards ARI)
        score = 0.5 * ari + 0.3 * purity + 0.2 * nmi
        
        explanation = f"Clustering quality: ARI={ari:.3f}, Purity={purity:.3f}, NMI={nmi:.3f}"
        
        evidence = {
            "system_clusters_count": len(system_clusters),
            "ground_truth_clusters_count": len(ground_truth_clusters),
            "adjusted_rand_index": ari,
            "purity": purity,
            "normalized_mutual_info": nmi
        }
        
        return MetricResult(
            score=score,
            explanation=explanation,
            evidence=evidence,
            details={
                "system_clusters": system_clusters,
                "ground_truth_clusters": ground_truth_clusters,
                "cluster_mapping": self._analyze_cluster_mapping(system_clusters, ground_truth_clusters)
            }
        )
    
    def _extract_system_clusters(self, run_result: Dict[str, Any]) -> List[Dict]:
        """Extract clusters from system output."""
        clusters = []
        
        # Look for cluster information in various possible locations
        opportunities = self._extract_artifact(run_result, "opportunities_structured")
        if opportunities and isinstance(opportunities, dict):
            if "clusters" in opportunities:
                clusters.extend(opportunities["clusters"])
            elif "opportunities" in opportunities:
                for opp in opportunities["opportunities"]:
                    if "cluster" in opp:
                        clusters.append(opp["cluster"])
        
        # Fallback: create single cluster if no clusters found
        if not clusters:
            pains = self._extract_artifact(run_result, "pains_structured")
            if pains and isinstance(pains, list):
                pain_ids = list(range(len(pains)))
                clusters.append({
                    "label": "default_cluster",
                    "pain_ids": pain_ids
                })
        
        return clusters
    
    def _extract_ground_truth_clusters(self, dataset: List[Dict]) -> List[Dict]:
        """Extract ground truth clusters from dataset."""
        all_clusters = []
        
        for item in dataset:
            gt_clusters = self._extract_ground_truth(item, "clusters")
            if gt_clusters and isinstance(gt_clusters, list):
                for cluster in gt_clusters:
                    cluster["dataset_id"] = item.get("id")
                    all_clusters.append(cluster)
        
        return all_clusters
    
    def _calculate_adjusted_rand_index(self, system_clusters: List[Dict], 
                                   ground_truth_clusters: List[Dict]) -> float:
        """Calculate Adjusted Rand Index."""
        # Create label assignments
        system_labels = self._create_label_assignment(system_clusters)
        gt_labels = self._create_label_assignment(ground_truth_clusters)
        
        # Ensure consistent labeling
        all_items = set(system_labels.keys()).union(set(gt_labels.keys()))
        
        system_label_list = [system_labels.get(item, -1) for item in all_items]
        gt_label_list = [gt_labels.get(item, -1) for item in all_items]
        
        # Calculate contingency table
        n = len(all_items)
        if n <= 1:
            return 1.0
        
        # Compute ARI using sklearn-like implementation
        from sklearn.metrics import adjusted_rand_score
        try:
            ari = adjusted_rand_score(gt_label_list, system_label_list)
            return max(0.0, ari)  # ARI can be negative
        except ImportError:
            # Fallback implementation
            return self._calculate_ari_fallback(system_label_list, gt_label_list)
    
    def _calculate_ari_fallback(self, system_labels: List[int], gt_labels: List[int]) -> float:
        """Fallback ARI calculation without sklearn."""
        from itertools import combinations
        
        n = len(system_labels)
        if n <= 1:
            return 1.0
        
        # Create pairs
        pairs = list(combinations(range(n), 2))
        
        # Count agreements
        tp = 0  # True positives (same in both)
        fp = 0  # False positives (same in system, different in GT)
        fn = 0  # False negatives (different in system, same in GT)
        tn = 0  # True negatives (different in both)
        
        for i, j in pairs:
            system_same = system_labels[i] == system_labels[j]
            gt_same = gt_labels[i] == gt_labels[j]
            
            if system_same and gt_same:
                tp += 1
            elif system_same and not gt_same:
                fp += 1
            elif not system_same and gt_same:
                fn += 1
            else:
                tn += 1
        
        # Calculate ARI
        total_pairs = len(pairs)
        if total_pairs == 0:
            return 1.0
        
        # Index values
        index = (tp + tn) / total_pairs
        expected_index = ((tp + fp) * (tp + fn) + (tn + fp) * (tn + fn)) / (total_pairs ** 2)
        max_index = ((tp + fp) * (tp + fn) + (tn + fp) * (tn + fn)) / (total_pairs ** 2)
        
        if max_index == expected_index:
            return 0.0
        
        ari = (index - expected_index) / (max_index - expected_index)
        return max(0.0, ari)
    
    def _calculate_purity(self, system_clusters: List[Dict], 
                         ground_truth_clusters: List[Dict]) -> float:
        """Calculate clustering purity."""
        system_labels = self._create_label_assignment(system_clusters)
        gt_labels = self._create_label_assignment(ground_truth_clusters)
        
        all_items = set(system_labels.keys()).union(set(gt_labels.keys()))
        
        if not all_items:
            return 1.0
        
        # Calculate purity for each system cluster
        total_correct = 0
        total_items = len(all_items)
        
        # Group items by system cluster
        system_groups = defaultdict(list)
        for item, cluster_id in system_labels.items():
            if item in all_items:
                system_groups[cluster_id].append(item)
        
        # Calculate purity
        for cluster_id, items in system_groups.items():
            if not items:
                continue
            
            # Find most common GT label in this cluster
            gt_labels_in_cluster = [gt_labels.get(item, -1) for item in items]
            if gt_labels_in_cluster:
                most_common = max(set(gt_labels_in_cluster), key=gt_labels_in_cluster.count)
                correct_count = gt_labels_in_cluster.count(most_common)
                total_correct += correct_count
        
        purity = total_correct / total_items if total_items > 0 else 1.0
        return purity
    
    def _calculate_normalized_mutual_info(self, system_clusters: List[Dict], 
                                       ground_truth_clusters: List[Dict]) -> float:
        """Calculate Normalized Mutual Information."""
        system_labels = self._create_label_assignment(system_clusters)
        gt_labels = self._create_label_assignment(ground_truth_clusters)
        
        all_items = set(system_labels.keys()).union(set(gt_labels.keys()))
        
        if not all_items:
            return 1.0
        
        system_label_list = [system_labels.get(item, -1) for item in all_items]
        gt_label_list = [gt_labels.get(item, -1) for item in all_items]
        
        try:
            from sklearn.metrics import normalized_mutual_info_score
            nmi = normalized_mutual_info_score(gt_label_list, system_label_list)
            return nmi
        except ImportError:
            # Fallback: simple entropy-based calculation
            return self._calculate_nmi_fallback(system_label_list, gt_label_list)
    
    def _calculate_nmi_fallback(self, system_labels: List[int], gt_labels: List[int]) -> float:
        """Fallback NMI calculation without sklearn."""
        from collections import Counter
        import math
        
        n = len(system_labels)
        if n <= 1:
            return 1.0
        
        # Calculate entropy for each labeling
        def entropy(labels):
            counts = Counter(labels)
            total = sum(counts.values())
            if total == 0:
                return 0.0
            
            ent = 0.0
            for count in counts.values():
                if count > 0:
                    p = count / total
                    ent -= p * math.log2(p)
            return ent
        
        H_system = entropy(system_labels)
        H_gt = entropy(gt_labels)
        
        # Calculate mutual information
        mi = 0.0
        joint_counts = Counter(zip(system_labels, gt_labels))
        
        for (s_label, gt_label), count in joint_counts.items():
            if count > 0:
                p_s = system_labels.count(s_label) / n
                p_gt = gt_labels.count(gt_label) / n
                p_joint = count / n
                mi += p_joint * math.log2(p_joint / (p_s * p_gt))
        
        # Normalize
        if H_system == 0 or H_gt == 0:
            return 1.0
        
        nmi = 2 * mi / (H_system + H_gt)
        return nmi
    
    def _create_label_assignment(self, clusters: List[Dict]) -> Dict[int, int]:
        """Create label assignment from clusters."""
        assignment = {}
        
        for cluster_idx, cluster in enumerate(clusters):
            pain_ids = cluster.get("pain_ids", [])
            for pain_id in pain_ids:
                assignment[pain_id] = cluster_idx
        
        return assignment
    
    def _analyze_cluster_mapping(self, system_clusters: List[Dict], 
                              ground_truth_clusters: List[Dict]) -> Dict[str, Any]:
        """Analyze mapping between system and ground truth clusters."""
        system_labels = self._create_label_assignment(system_clusters)
        gt_labels = self._create_label_assignment(ground_truth_clusters)
        
        all_items = set(system_labels.keys()).union(set(gt_labels.keys()))
        
        mapping = defaultdict(lambda: defaultdict(int))
        
        for item in all_items:
            sys_cluster = system_labels.get(item, -1)
            gt_cluster = gt_labels.get(item, -1)
            mapping[sys_cluster][gt_cluster] += 1
        
        return {
            "mapping": dict(mapping),
            "dominant_mappings": {
                sys_cluster: max(gt_clusters.items(), key=lambda x: x[1])[0]
                for sys_cluster, gt_clusters in mapping.items()
            }
        }
    
    def get_required_artifacts(self) -> List[str]:
        """Get required artifacts for this metric."""
        return ["opportunities_structured", "pains_structured"]
    
    def get_required_ground_truth(self) -> List[str]:
        """Get required ground truth fields."""
        return ["clusters"]
