#!/bin/bash

# List of packages to install (format: package:version, or just package)
PACKAGES="python:3.12.2,graphviz,git"

# Function to check if a package is installed
check_package() {
  local pkg_name=$1
  local pkg_version=$2

  # Check if package is installed (distro-agnostic where possible)
  if command -v dpkg >/dev/null 2>&1; then
    # Debian/Ubuntu
    if dpkg -l | grep -qw "$pkg_name"; then
      if [ -n "$pkg_version" ]; then
        installed_version=$(dpkg -l | grep "$pkg_name" | awk '{print $3}' | head -1)
        if [ "$installed_version" = "$pkg_version" ]; then
          echo "$pkg_name $pkg_version is already installed."
          return 0
        else
          echo "$pkg_name is installed but version ($installed_version) does not match required ($pkg_version)."
          return 1
        fi
      else
        echo "$pkg_name is already installed."
        return 0
      fi
    fi
  elif command -v rpm >/dev/null 2>&1; then
    # CentOS/RHEL/Fedora/AlmaLinux
    if rpm -q "$pkg_name" >/dev/null 2>&1; then
      if [ -n "$pkg_version" ]; then
        installed_version=$(rpm -q "$pkg_name" --qf '%{VERSION}' | head -1)
        if [ "$installed_version" = "$pkg_version" ]; then
          echo "$pkg_name $pkg_version is already installed."
          return 0
        else
          echo "$pkg_name is installed but version ($installed_version) does not match required ($pkg_version)."
          return 1
        fi
      else
        echo "$pkg_name is already installed."
        return 0
      fi
    fi
  else
    echo "Unsupported package manager for checking $pkg_name."
    return 1
  fi
  return 1
}

# Function to install packages based on distro
install_package() {
  local pkg_name=$1
  local pkg_version=$2
  local distro=$3

  case $distro in
    "debian"|"ubuntu")
      if [ -n "$pkg_version" ]; then
        sudo apt-get install -y "${pkg_name}=${pkg_version}"
      else
        sudo apt-get install -y "$pkg_name"
      fi
      ;;
    "centos"|"rhel"|"almalinux")
      if [ -n "$pkg_version" ]; then
        sudo yum install -y "${pkg_name}-${pkg_version}"
      else
        sudo yum install -y "$pkg_name"
      fi
      ;;
    "fedora")
      if [ -n "$pkg_version" ]; then
        sudo dnf install -y "${pkg_name}-${pkg_version}"
      else
        sudo dnf install -y "$pkg_name"
      fi
      ;;
    *)
      echo "Unsupported distribution: $distro"
      exit 1
      ;;
  esac
}

# Detect the Linux distribution
if [ -f /etc/os-release ]; then
  . /etc/os-release
  DISTRO=$(echo "$ID" | tr '[:upper:]' '[:lower:]')
else
  echo "Cannot detect distribution. /etc/os-release not found."
  exit 1
fi

# Update package lists for supported distributions
case $DISTRO in
  "debian"|"ubuntu")
    sudo apt-get update
    ;;
  "centos"|"rhel"|"almalinux")
    sudo yum makecache
    ;;
  "fedora")
    sudo dnf makecache
    ;;
  *)
    echo "Unsupported distribution: $DISTRO"
    exit 1
    ;;
esac

# Convert PACKAGES string to array and process each package
IFS=',' read -ra PKG_LIST <<< "$PACKAGES"
for pkg in "${PKG_LIST[@]}"; do
  # Split package name and version (if provided)
  pkg_name=$(echo "$pkg" | cut -d':' -f1)
  pkg_version=$(echo "$pkg" | cut -s -d':' -f2)

  # Map 'python' to distro-specific package name
  if [ "$pkg_name" = "python" ]; then
    case $DISTRO in
      "debian"|"ubuntu")
        pkg_name="python3"
        ;;
      "centos"|"rhel"|"almalinux"|"fedora")
        pkg_name="python3"
        ;;
    esac
  fi

  # Check if package is installed
  if ! check_package "$pkg_name" "$pkg_version"; then
    echo "Installing $pkg_name${pkg_version:+ version $pkg_version}..."
    install_package "$pkg_name" "$pkg_version" "$DISTRO"
    if [ $? -eq 0 ]; then
      echo "$pkg_name${pkg_version:+ version $pkg_version} installed successfully."
    else
      echo "Failed to install $pkg_name${pkg_version:+ version $pkg_version}."
      exit 1
    fi
  fi
done

echo "All required packages are installed."