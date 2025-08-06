import os
import pandas as pd
import numpy as np
from collections import defaultdict


# 计算 Jaccard 指数
def jaccard_index(set1, set2):
    return len(set1 & set2) / len(set1 | set2)


# 计算随机期望值
def random_expectation(size1, size2, total_size):
    return (size1 * size2) / total_size


# 调整后的 Jaccard 指数
def adjusted_jaccard(j, j_expect):
    print(f"Jaccard Index: {j}, Random Expectation: {j_expect}")
    if j <= j_expect:
        return 0
    return (j - j_expect) / (1 - j_expect)


# 加载一个时间片的社区数据
def load_community_data(file_path):
    df = pd.read_csv(file_path)
    communities = defaultdict(set)
    for _, row in df.iterrows():
        communities[row['community']].add(row['id'])
    return communities


# 主函数：追踪社区变化
def track_community_changes(root_dir, threshold=0.5):
    # 获取所有日期文件夹
    dates = sorted([f for f in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, f))])

    # 存储所有时间片社区
    all_communities = {}
    total_nodes = 0

    for date in dates:
        file_path = os.path.join(root_dir, date, "handle", f"rank{date}.csv")
        if os.path.exists(file_path):
            communities = load_community_data(file_path)
            all_communities[date] = communities
            total_nodes += sum(len(nodes) for nodes in communities.values())
        else:
            print(f"Warning: File {file_path} does not exist.")

    # 开始分析社区变化
    changes = []
    prev_date = None
    for date in dates:
        if date not in all_communities:
            continue  # 跳过缺少数据的时间片

        if prev_date is None:
            prev_date = date
            continue

        prev_communities = all_communities[prev_date]
        current_communities = all_communities[date]
        total_size = total_nodes

        # 计算相似性矩阵
        similarity_matrix = []
        for prev_comm_id, prev_nodes in prev_communities.items():
            row = []
            for curr_comm_id, curr_nodes in current_communities.items():
                j = jaccard_index(prev_nodes, curr_nodes)
                j_expect = random_expectation(len(prev_nodes), len(curr_nodes), total_size)
                adj_j = adjusted_jaccard(j, j_expect)
                row.append(adj_j)
            similarity_matrix.append(row)

        similarity_matrix = np.array(similarity_matrix)

        # 确定延续关系
        for i, prev_comm_id in enumerate(prev_communities.keys()):
            for j, curr_comm_id in enumerate(current_communities.keys()):
                if similarity_matrix[i, j] >= threshold:
                    changes.append({
                        "prev_date": prev_date,
                        "prev_community": prev_comm_id,
                        "current_date": date,
                        "current_community": curr_comm_id,
                        "similarity": similarity_matrix[i, j]
                    })

        prev_date = date

    # 转换为 DataFrame
    changes_df = pd.DataFrame(changes)
    return changes_df


# 调用主函数
data_directory = "."  # 当前目录
threshold = 0  # 相似度阈值
changes_df = track_community_changes(data_directory, threshold)

# 输出结果
print(changes_df)
changes_df.to_csv("community_changes.csv", index=False)
