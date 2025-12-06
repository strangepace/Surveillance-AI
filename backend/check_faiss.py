import sys
try:
    import faiss
    print(f"✅ FAISS is installed (version: {faiss.__version__ if hasattr(faiss, '__version__') else 'unknown'})")
    sys.exit(0)
except ImportError:
    print("❌ FAISS is NOT installed")
    print("\nInstalling faiss-cpu...")
    import subprocess
    result = subprocess.run([sys.executable, "-m", "pip", "install", "faiss-cpu"], 
                          capture_output=True, text=True)
    print(result.stdout)
    if result.returncode == 0:
        print("✅ FAISS installed successfully!")
        try:
            import faiss
            print(f"✅ Verified: FAISS is now available")
        except ImportError:
            print("❌ Still cannot import FAISS after installation")
            sys.exit(1)
    else:
        print("❌ Installation failed:")
        print(result.stderr)
        sys.exit(1)

