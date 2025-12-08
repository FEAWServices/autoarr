## 🚀 Installation

### Docker (Recommended)

#### Docker Hub

```bash
docker pull autoarr/autoarr:latest
docker-compose -f docker/docker-compose.production.yml up -d
```

#### GitHub Container Registry

```bash
docker pull ghcr.io/feawservices/autoarr:latest
docker-compose -f docker/docker-compose.production.yml up -d
```

### Native Executables

Download platform-specific executables from the Assets section below:

- **Linux (x64)**: `autoarr-linux-x64-{version}.tar.gz`
- **Windows (x64)**: `autoarr-windows-x64-{version}.zip`
- **macOS (Intel)**: `autoarr-macos-x64-{version}.tar.gz`
- **macOS (ARM)**: `autoarr-macos-arm64-{version}.tar.gz`

Extract and run:

```bash
# Linux/macOS
tar -xzf autoarr-linux-x64-{version}.tar.gz
cd autoarr
./autoarr

# Windows
# Extract the zip file
# Run autoarr.exe
```

### Verify Checksums

Download `SHA256SUMS.txt` and verify:

```bash
sha256sum -c SHA256SUMS.txt
```

## 📚 Documentation

- **Quick Start**: [docs/QUICK-START.md](https://github.com/FEAWServices/autoarr/blob/main/docs/QUICK-START.md)
- **Configuration**: [docs/CONFIGURATION.md](https://github.com/FEAWServices/autoarr/blob/main/docs/CONFIGURATION.md)
- **Troubleshooting**: [docs/TROUBLESHOOTING.md](https://github.com/FEAWServices/autoarr/blob/main/docs/TROUBLESHOOTING.md)

---

## 📝 Changelog
