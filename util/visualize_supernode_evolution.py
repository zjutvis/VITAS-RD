import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from matplotlib.animation import FuncAnimation
import matplotlib.cm as cm
import hashlib


def create_supernode_evolution_visualization(dates):
    """
    Visualize superNode angle evolution across all months.

    Args:
        dates: list of date keys like ["202401", "202402", ...]
    """
    plt.figure(figsize=(15, 10))

    # Collect all organizations (e.g., countries)
    all_organizations = set()
    community_organizations = {}

    for date in dates:
        try:
            data_path = f'../visualization/assets/data/{date}/handle/superNode_with_angle.csv'
            if os.path.exists(data_path):
                data = pd.read_csv(data_path)
                if 'organization' in data.columns:
                    all_organizations.update(data['organization'].dropna().unique().tolist())
                    for _, row in data.iterrows():
                        if pd.notna(row.get('organization')):
                            community_organizations[int(row['community'])] = row['organization']
        except Exception as e:
            print(f"Error loading data for {date}: {str(e)}")

    # Assign colors for organizations
    organization_colors = {}
    cmap = cm.get_cmap('tab20', len(all_organizations) if len(all_organizations) > 0 else 20)

    for i, org in enumerate(sorted(all_organizations)):
        organization_colors[org] = cmap(i)

    # Color mapping for communities without organization info
    def get_color_for_community(comm_id, org=None):
        if org and org in organization_colors:
            return organization_colors[org]

        # Stable color based on community ID
        hash_value = int(hashlib.md5(str(comm_id).encode()).hexdigest(), 16)
        return cmap(hash_value % 20)

    # Angle ticks and guide lines
    for angle in range(0, 360, 30):
        angle_rad = np.radians(angle)
        x_end = np.cos(angle_rad) * 10
        y_end = np.sin(angle_rad) * 10
        plt.plot([0, x_end], [0, y_end], 'gray', linestyle='--', alpha=0.3)
        plt.text(x_end * 1.1, y_end * 1.1, f"{angle}°", fontsize=8, color='gray')

    # Axes
    plt.axhline(y=0, color='k', linestyle='-', alpha=0.3)
    plt.axvline(x=0, color='k', linestyle='-', alpha=0.3)

    # Track trajectories per community
    community_trajectories = {}

    # Add monthly data points
    for i, date in enumerate(dates):
        try:
            data_path = f'../visualization/assets/data/{date}/handle/superNode_with_angle.csv'
            if not os.path.exists(data_path):
                continue

            data = pd.read_csv(data_path)

            # Normalized distance factor (kept for future scaling needs)
            max_distance = data['distance'].max()
            if max_distance > 0:
                normalized_factor = 8 / max_distance  # max radius = 8 (unused below)
            else:
                normalized_factor = 1

            # Plot each community
            for _, row in data.iterrows():
                comm = int(row['community'])
                angle_rad = np.radians(row['angle'])

                # Use month index as radial distance to form concentric rings
                radius = 2 + i * 0.8

                # Polar -> Cartesian
                x = radius * np.cos(angle_rad)
                y = radius * np.sin(angle_rad)

                # Size from community size if available
                size = np.sqrt(row['size']) / 20 if 'size' in row else 20

                # Organization label (if any)
                org = row.get('organization') if 'organization' in row.columns else None
                if pd.isna(org):
                    org = community_organizations.get(comm)

                # Draw point
                color = get_color_for_community(comm, org)
                plt.scatter(x, y, s=size, color=color, alpha=0.7, edgecolors='black', linewidth=0.5)

                # Label community ID
                plt.text(x, y, str(comm), fontsize=8, ha='center', va='center')

                # Track trajectory
                if comm not in community_trajectories:
                    community_trajectories[comm] = {'points': [], 'org': org}
                community_trajectories[comm]['points'].append((x, y))
                if not community_trajectories[comm]['org'] and org:
                    community_trajectories[comm]['org'] = org

        except Exception as e:
            print(f"Error processing {date}: {str(e)}")

    # Plot trajectories
    for comm, data in community_trajectories.items():
        points = data['points']
        org = data['org']
        if len(points) > 1:
            x_vals, y_vals = zip(*points)
            color = get_color_for_community(comm, org)
            plt.plot(x_vals, y_vals, '-', color=color, alpha=0.5, linewidth=1)

    # Month labels and rings
    for i, date in enumerate(dates):
        radius = 2 + i * 0.8
        plt.text(0, -radius - 0.3, date, ha='center', fontsize=9)
        circle = plt.Circle((0, 0), radius, fill=False, color='gray', linestyle='-', alpha=0.2)
        plt.gca().add_patch(circle)

    # Legend by organization
    handles = []
    labels = []
    for org in sorted(all_organizations):
        if org and not pd.isna(org) and org != "Unknown":
            handles.append(
                plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=organization_colors[org], markersize=8)
            )
            labels.append(org)

    if handles:
        plt.legend(handles, labels, title='Organization (Country)', loc='upper right', bbox_to_anchor=(1.1, 1), fontsize=8)

    # Figure settings
    plt.grid(True, alpha=0.3)
    plt.title('Community Angle Evolution (Jan–Oct 2024)')
    plt.axis('equal')
    plt.tight_layout()

    # Save figure
    os.makedirs('../visualization/assets/data/images', exist_ok=True)
    plt.savefig('../visualization/assets/data/images/community_angle_evolution.png', dpi=300)
    plt.show()


if __name__ == "__main__":
    dates = [f"20240{i}" for i in range(1, 10)] + ["202410"]
    create_supernode_evolution_visualization(dates)
