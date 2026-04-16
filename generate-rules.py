name: Build BT/PT/Download Rules

on:
  workflow_dispatch:
    inputs:
      force_build:
        description: 'Force rebuild (skip diff check)'
        required: false
        default: 'false'
        type: boolean
  schedule:
    - cron: '0 0 1 * *'    # 每月1号自动更新

permissions:
  contents: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Generate Rules
        id: gen
        run: |
          set -x
          python3 --version
          ls -la generate-rules.py
          python3 generate-rules.py --output rules/
        env:
          PYTHONUNBUFFERED: '1'

      - name: List generated files
        if: always()
        run: |
          echo "=== rules/ directory ==="
          ls -la rules/ 2>/dev/null || echo "rules/ directory is empty or missing"
          for f in rules/*.txt; do
            [ -f "$f" ] && echo "  $f: $(wc -l < "$f") lines"
          done

      - name: Check changes
        id: diff
        run: |
          git add rules/

          if [[ "${{ inputs.force_build }}" == "true" ]]; then
            echo "changed=true" >> $GITHUB_OUTPUT
          else
            git diff --cached --quiet && echo "changed=false" >> $GITHUB_OUTPUT || echo "changed=true" >> $GITHUB_OUTPUT
          fi

          # 变更摘要
          echo "### BT/PT/Download Rules Update" > /tmp/summary.md
          echo "" >> /tmp/summary.md
          echo "| 规则集 | 条数 |" >> /tmp/summary.md
          echo "|--------|------|" >> /tmp/summary.md
          for f in rules/*.txt; do
            [ -f "$f" ] && echo "| $(basename $f) | $(wc -l < "$f") |" >> /tmp/summary.md
          done
          echo "" >> /tmp/summary.md
          echo '```diff' >> /tmp/summary.md
          git diff --cached --stat >> /tmp/summary.md 2>/dev/null || echo "(no diff)" >> /tmp/summary.md
          echo '```' >> /tmp/summary.md
          cat /tmp/summary.md >> $GITHUB_STEP_SUMMARY

      - name: Commit & Push
        if: steps.diff.outputs.changed == 'true'
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "actions@github.com"

          git commit -m "auto: update BT/PT/Download rules $(date +%Y-%m-%d)"
          git push
