"""Episode sampler for few-shot learning — contains support/query overlap bug."""
import torch
import numpy as np


class EpisodeSampler:
    """Samples N-way K-shot episodes from a dataset.

    BUG: The query set is sampled using the same indices as the support set,
    causing support/query overlap. The model can trivially "look up" the answer
    during training, leading to overestimated training accuracy and poor test
    generalization.

    Correct behavior: query samples must be DIFFERENT from support samples.
    After selecting K support samples per class, the remaining samples of that
    class should be used to draw the query samples.
    """

    def __init__(self, n_way: int = 5, k_shot: int = 5,
                 n_query: int = 10):
        self.n_way = n_way
        self.k_shot = k_shot
        self.n_query = n_query

    def sample_episode(self, class_data: dict) -> dict:
        """Sample one episode with N-way K-shot support and N-way n_query query.

        Args:
            class_data: dict mapping class_id -> tensor of shape (n_samples, input_dim)

        Returns:
            dict with support, query, support_labels, query_labels
        """
        # Sample N classes
        all_classes = list(class_data.keys())
        episode_classes = np.random.choice(all_classes, self.n_way, replace=False)

        support_list, query_list = [], []
        support_labels, query_labels = [], []

        for label_idx, cls in enumerate(episode_classes):
            samples = class_data[cls]
            n_available = len(samples)

            # Sample K+n_query indices — should be all unique
            total_needed = self.k_shot + self.n_query
            perm = torch.randperm(min(n_available, total_needed + 5))[:total_needed]

            support_idx = perm[:self.k_shot]

            # BUG: query uses the SAME indices as support
            # Correct: query_idx = perm[self.k_shot:self.k_shot + self.n_query]
            query_idx = perm[:self.n_query]  # BUG: overlaps with support_idx when n_query <= k_shot or same perm

            support_list.append(samples[support_idx])
            query_list.append(samples[query_idx])
            support_labels.extend([label_idx] * self.k_shot)
            query_labels.extend([label_idx] * self.n_query)

        support = torch.cat(support_list, dim=0)  # (N*K, D)
        query = torch.cat(query_list, dim=0)       # (N*Q, D)
        support_labels = torch.tensor(support_labels, dtype=torch.long)
        query_labels = torch.tensor(query_labels, dtype=torch.long)

        return {
            "support": support,
            "query": query,
            "support_labels": support_labels,
            "query_labels": query_labels,
            "episode_classes": episode_classes,
        }
