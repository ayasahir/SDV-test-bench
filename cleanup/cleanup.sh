#!/bin/bash

# Cleanup script to reset Raspberry Pi to neutral state for SDV testbench
echo "Starting cleanup of SDV testbench on Raspberry Pi..."

# Step 1: Stop and uninstall k3s (Kubernetes)
echo "Removing k3s (Kubernetes)..."
if [ -f /usr/local/bin/k3s-uninstall.sh ]; then
    sudo /usr/local/bin/k3s-uninstall.sh
    echo "k3s master node uninstalled."
elif [ -f /usr/local/bin/k3s-agent-uninstall.sh ]; then
    sudo /usr/local/bin/k3s-agent-uninstall.sh
    echo "k3s worker node uninstalled."
else
    echo "No k3s installation found."
fi

# Step 2: Remove Docker containers and images
echo "Removing Docker containers and images..."
sudo docker ps -a -q | xargs -r sudo docker rm -f
sudo docker images -q | sort -u | xargs -r sudo docker rmi -f
echo "Docker containers and images removed."

# Step 3: Remove SDV-related files
echo "Removing SDV-related files..."
sudo rm -rf /tmp/axil.log
sudo rm -rf /tmp/sdv_metrics_*.json
sudo rm -rf /tmp/vehicle_simulation_*.json
sudo rm -rf ~/sdv-testbench
sudo rm -rf ~/k8s-manifests
sudo rm -rf ~/docker
echo "SDV log and metric files removed."

# Step 5: Clean up Kubernetes config
echo "Removing Kubernetes configuration..."
sudo rm -rf ~/.kube
echo "Kubernetes configuration removed."

# Step 6: Remove Docker
echo "Removing Docker..."
sudo apt purge -y docker.io 2>/dev/null
sudo rm -rf /var/lib/docker
echo "Docker removed."

# Step 7: Changing hostname
echo "Enter new hostname:"
read new_hostname
sudo hostnamectl set-hostname "$new_hostname"
echo "$new_hostname" | sudo tee /etc/hostname
sudo sed -i "s/127.0.1.1 .*/127.0.1.1 $new_hostname/" /etc/hosts
echo "Hostname changed to $new_hostname "

# Step 8: Reboot (optional, recommended)
echo "Cleanup complete! run  "sudo reboot" to reboot Raspberry Pi (recommended)..."