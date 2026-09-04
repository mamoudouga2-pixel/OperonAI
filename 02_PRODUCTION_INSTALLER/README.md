# Installer packaging

This directory contains build-entry documentation and packaging metadata. The runtime module remains unprivileged by design.

Recommended production builders:
- Windows: package the launcher with PyInstaller and wrap with WiX/MSI; request elevation only for machine-wide install.
- macOS: package app bundle with PyInstaller/briefcase and sign/notarize it; use pkg/dmg for distribution.
- Linux: ship AppImage or a distro package. Keep user-scoped default installation available.

The generated deployment manifest must pin every external artifact URL, SHA-256 and (where supported) an Ed25519 signature/public key.
