import reflex as rx

config = rx.Config(
    app_name="reflex_dapp",
    frontend_port=3000,
    backend_port=8000,
    # Disable sitemap plugin to avoid warnings in newer Reflex versions
    disable_plugins=["reflex.plugins.sitemap.SitemapPlugin"],
)