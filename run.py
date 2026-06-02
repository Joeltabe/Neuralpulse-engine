#!/usr/bin/env python3
import uvicorn
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"

    print(f"""
    =======================================
     NeuralPulse Engine v1.0
     Neuromarketing SaaS — TRIBE v2 Powered
    =======================================
     API:         http://{host}:{port}
     Docs:        http://{host}:{port}/docs
     Landing:     http://{host}:{port}/
     Dashboard:   http://{host}:{port}/app/dashboard.html
    =======================================
    """)

    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
