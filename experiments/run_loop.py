"""Kaggle experiment loop driver.

Auth: reads the API token from ~/.kaggle/access_token (kaggle CLI >= 1.8).

Usage:
    python run_loop.py push      # rebuild ipynb (jupytext + kernelspec), push kernel
    python run_loop.py status    # check run status
    python run_loop.py pull      # download outputs into experiments/results/
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
KDIR = os.path.join(HERE, "kaggle")
META = os.path.join(KDIR, "kernel-metadata.json")
RESULTS = os.path.join(HERE, "results")


def kernel_id():
    with open(META) as f:
        return json.load(f)["id"]


def cmd(args):
    print("+", " ".join(args))
    r = subprocess.run(args, capture_output=True, text=True)
    print(r.stdout)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
    return r


def build():
    """py -> ipynb via jupytext, then add the kernelspec Kaggle's papermill requires."""
    src = os.path.join(KDIR, "svg_gates_v1.py")
    nb_path = os.path.join(KDIR, "svg_gates_v1.ipynb")
    cmd([sys.executable, "-m", "jupytext", "--to", "ipynb", src])
    with open(nb_path, encoding="utf-8") as f:
        nb = json.load(f)
    nb["metadata"]["kernelspec"] = {"name": "python3", "display_name": "Python 3",
                                    "language": "python"}
    nb["metadata"]["language_info"] = {"name": "python", "version": "3.12"}
    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1)


def push():
    build()
    os.environ["PYTHONUTF8"] = "1"
    cmd([sys.executable, "-m", "kaggle", "kernels", "push", "-p", KDIR])


def status():
    cmd([sys.executable, "-m", "kaggle", "kernels", "status", kernel_id()])


def pull():
    os.makedirs(RESULTS, exist_ok=True)
    cmd([sys.executable, "-m", "kaggle", "kernels", "output", kernel_id(), "-p", RESULTS])


if __name__ == "__main__":
    {"push": push, "status": status, "pull": pull}[sys.argv[1]]()
