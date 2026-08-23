#!/bin/bash
# ============================================================
# PINOCCHIO — Full Pre-Hackathon Setup Script
# Run from: ~/Documents/YC-GREPTILE/
# ============================================================

set -e  # Exit on any error

echo "============================================"
echo "  🤥 PINOCCHIO — Pre-Hackathon Setup"
echo "============================================"
echo ""

# ─────────────────────────────────────────────
# STEP 0: Check prerequisites
# ─────────────────────────────────────────────
echo "▸ Step 0: Checking prerequisites..."

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "  ✗ Node.js not found. Installing via nvm..."
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    nvm install 22
    nvm use 22
else
    NODE_VERSION=$(node --version)
    echo "  ✓ Node.js $NODE_VERSION found"
fi

# Check npm
if ! command -v npm &> /dev/null; then
    echo "  ✗ npm not found. Install Node.js first."
    exit 1
else
    echo "  ✓ npm $(npm --version) found"
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "  ✗ Python3 not found. Please install Python 3.11+."
    exit 1
else
    echo "  ✓ Python3 $(python3 --version) found"
fi

# Check git
if ! command -v git &> /dev/null; then
    echo "  ✗ git not found. Please install git."
    exit 1
else
    echo "  ✓ git $(git --version | cut -d' ' -f3) found"
fi

echo ""

# ─────────────────────────────────────────────
# STEP 1: Install Codex CLI
# ─────────────────────────────────────────────
echo "▸ Step 1: Installing OpenAI Codex CLI..."
echo "  ⚠ IMPORTANT: Package is @openai/codex, NOT 'codex'"

if command -v codex &> /dev/null; then
    echo "  ✓ Codex CLI already installed: $(codex --version 2>/dev/null || echo 'version check failed')"
else
    npm install -g @openai/codex
    echo "  ✓ Codex CLI installed"
fi

echo ""
echo "  → Now run manually: codex login"
echo "    Select 'Sign in with ChatGPT' and use your PERSONAL workspace."
echo "    (Do NOT use a Business or managed workspace — credits won't redeem.)"
echo ""

# ─────────────────────────────────────────────
# STEP 2: Install Claude Code
# ─────────────────────────────────────────────
echo "▸ Step 2: Installing Claude Code..."

if command -v claude &> /dev/null; then
    echo "  ✓ Claude Code already installed"
else
    npm install -g @anthropic-ai/claude-code
    echo "  ✓ Claude Code installed"
fi

echo ""
echo "  → Now run manually: claude login"
echo ""

# ─────────────────────────────────────────────
# STEP 3: Install Claude-Mem
# ─────────────────────────────────────────────
echo "▸ Step 3: Installing Claude-Mem..."
echo "  ⚠ IMPORTANT: Use npx, NOT npm install -g"
echo ""
echo "  → Run manually: npx claude-mem install"
echo "    (Interactive installer — needs your input)"
echo ""
echo "  After install, restart Claude Code, then verify:"
echo "    - Worker running: check http://127.0.0.1:<port>"
echo "    - Port is in: ~/.claude-mem/settings.json"
echo ""

# ─────────────────────────────────────────────
# STEP 4: Create project structure
# ─────────────────────────────────────────────
echo "▸ Step 4: Creating Pinocchio project structure..."

PROJECT_DIR="$(pwd)/pinocchio"
mkdir -p "$PROJECT_DIR"
mkdir -p "$PROJECT_DIR/prompts"
mkdir -p "$PROJECT_DIR/checks"

echo "  ✓ Created $PROJECT_DIR"

# ─────────────────────────────────────────────
# STEP 5: Python virtual environment + deps
# ─────────────────────────────────────────────
echo "▸ Step 5: Setting up Python environment..."

cd "$PROJECT_DIR"
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install rich unidiff openai anthropic gitpython requests

# Save requirements
pip freeze > requirements.txt

echo "  ✓ Virtual environment created and dependencies installed"
echo ""

# ─────────────────────────────────────────────
# STEP 6: Create demo repo (the trap)
# ─────────────────────────────────────────────
echo "▸ Step 6: Creating demo repo with trap task..."

DEMO_DIR="$(pwd)/../demo-repo"
mkdir -p "$DEMO_DIR"
cd "$DEMO_DIR"
git init

echo "  ✓ Demo repo created at $DEMO_DIR"
echo ""

# Go back to project root
cd "$(pwd)/../"

# ─────────────────────────────────────────────
# STEP 7: Initialize git for pinocchio
# ─────────────────────────────────────────────
echo "▸ Step 7: Initializing git for pinocchio..."

cd "$PROJECT_DIR"
git init

echo "  ✓ Git initialized"
echo ""

echo "============================================"
echo "  ✓ AUTOMATED SETUP COMPLETE"
echo "============================================"
echo ""
echo "  MANUAL STEPS REMAINING:"
echo "  1. codex login          (sign in with ChatGPT personal workspace)"
echo "  2. claude login         (sign in with Anthropic account)"
echo "  3. npx claude-mem install  (interactive installer)"
echo "  4. Test: codex 'say hello' in any git repo"
echo "  5. Test: claude 'say hello'"
echo "  6. Verify claude-mem worker is running"
echo ""
echo "  YOUR PROJECT IS AT: $PROJECT_DIR"
echo "  YOUR DEMO REPO IS AT: $(realpath ../demo-repo)"
echo ""
echo "  Next: The setup script has created project files."
echo "  Review CLAUDE.md, prompts/all-prompts.md, and demo-repo/"
echo "============================================"
