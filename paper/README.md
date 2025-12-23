## Paper (ACL template content, ready to paste into Overleaf)

This folder provides two ways to use the paper in Overleaf:

### 1) Fastest: single-file paste
- Open `paper/acl_submission.tex`
- Copy all content into your Overleaf main file (usually `acl_latex.tex`)
- Upload figures from `paper/figures/` to Overleaf (or import this repo to Overleaf via GitHub)

### 2) Cleaner: multi-file project
- Use `paper/main.tex` as the Overleaf main file
- Keep section files in `paper/sections/`
- Keep tables in `paper/tables/`

### Generate/update tables + copy figures
From repo root:

```bash
python scripts/export_paper_assets.py
```

It will:
- write LaTeX tables into `paper/tables/`
- copy plots from `results/visualizations/` into `paper/figures/`


