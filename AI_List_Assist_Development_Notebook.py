# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.1
# ---

# %% [markdown]
# # AI List Assist | Developer Architecture Portal

# %%
from IPython.display import HTML, display

# Encapsulating the raw HTML/JS/CSS as a Python string so the kernel can render it natively
dev_portal_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI List Assist | Developer Architecture Portal</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #F8FAFC; color: #1E293B; }
        .glass-card { background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); border: 1px solid #E2E8F0; }
        .flow-arrow::after {
            content: ''; position: absolute; right: -20px; top: 50%; transform: translateY(-50%);
            border-width: 8px 0 8px 12px; border-color: transparent transparent transparent #CBD5E1;
        }
        .active-node { border-color: #3B82F6; background-color: #EFF6FF; }
        .chart-container { position: relative; width: 100%; height: 300px; max-width: 600px; margin: 0 auto; }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #F1F5F9; }
        ::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #94A3B8; }
        .code-block { font-family: 'Fira Code', monospace; }
    </style>
</head>
<body class="min-h-screen flex flex-col">

    <header class="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold">AI</div>
                <div>
                    <h1 class="text-lg font-bold tracking-tight text-slate-900">List Assist <span class="text-slate-400 font-normal">| DevPortal</span></h1>
                    <p class="text-xs text-emerald-600 font-medium flex items-center gap-1">
                        <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                        Active Dev v2.2
                    </p>
                </div>
            </div>
            <nav class="hidden md:flex gap-6 text-sm font-medium text-slate-600">
                <a href="#pipeline" class="hover:text-blue-600 transition">Logic Pipeline</a>
                <a href="#architecture" class="hover:text-blue-600 transition">System Arch</a>
                <a href="#roadmap" class="hover:text-blue-600 transition">Roadmap</a>
                <a href="#setup" class="hover:text-blue-600 transition">Setup</a>
            </nav>
        </div>
    </header>

    <main class="flex-grow max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full space-y-12">
        <section class="text-center space-y-4">
            <h2 class="text-4xl font-extrabold text-slate-900 tracking-tight sm:text-5xl">Programmatic Resale Automation</h2>
            <p class="max-w-2xl mx-auto text-lg text-slate-600">
                An enterprise-grade orchestration layer bridging unstructured visual data and structured e-commerce requirements using Hybrid AI.
            </p>
        </section>
    </main>

</body>
</html>
"""

# Render the HTML inside the Notebook output cell
display(HTML(dev_portal_html))

# %% [markdown]
# # Google Drive Mounting (Colab Only)
# Note: Since we are running in WSL2 Ubuntu locally, this cell will fail if executed on your local machine.

# %%
try:
    from google.colab import drive
    drive.mount('/content/drive')
except ImportError:
    print("Not running in Google Colab. Skipping Drive mount.")
