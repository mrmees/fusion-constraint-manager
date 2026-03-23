# Technology Stack

**Analysis Date:** 2026-03-22

## Languages

**Primary:**
- Python 3.x - Add-in implementation, command handlers, constraint logic
- JSON - Add-in manifest configuration

**Secondary:**
- PNG - Toolbar icon assets

## Runtime

**Environment:**
- Autodesk Fusion 360 (2025+) - Required host application
- Windows / macOS - Supported platforms per manifest

**Package Manager:**
- pip (Python standard) - For development and testing dependencies only
- No lockfile (`requirements.txt` or similar) - Pure Python standard library used, no production dependencies

## Frameworks

**Core:**
- Autodesk Fusion 360 API (adsk.core, adsk.fusion) - Desktop add-in framework and geometric modeling API
  - No version specified; loads what Fusion provides at runtime

**Testing:**
- pytest - For unit testing constraint logic outside Fusion
  - Run with: `python -m pytest ConstraintManager/tests/ -v`

**Build/Dev:**
- No build tool - Add-in is pure Python; direct folder copy to installation directory required

## Key Dependencies

**Critical:**
- `adsk.core` - Fusion application framework, UI command definitions, event handlers
- `adsk.fusion` - Fusion modeling API, sketch/constraint objects, design traversal

**Development Only:**
- `pytest` - Test execution; not included in production add-in

## Configuration

**Environment:**
- Windows: `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\ConstraintManager\`
- macOS: `/Users/[user]/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/ConstraintManager/`
- Installation is folder copy, no build step

**Build:**
- No build system - manifest file `ConstraintManager.manifest` declares metadata (name, version, author, supported OS)

## Platform Requirements

**Development:**
- Python 3.x installed locally (for running tests outside Fusion)
- pytest package (development only)
- Windows or macOS (no Linux/WSL support — Fusion is desktop-only)

**Production:**
- Autodesk Fusion 360 application installed and running
- Windows or macOS as per Fusion support
- No internet connection required — fully offline add-in

---

*Stack analysis: 2026-03-22*
