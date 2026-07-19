"""Kaggle experiment loop driver (generic over experiment directories).

Auth: reads the API token from ~/.kaggle/access_token (kaggle CLI >= 1.8).

Usage:
    python run_loop.py push   [kernel_dir]   # jupytext build + kernelspec + push (T4)
    python run_loop.py status [kernel_dir]
    python run_loop.py pull   [kernel_dir] [dest]

kernel_dir defaults to ./kaggle (the v1-scope experiment); pass e.g. m1/kaggle
for the M1 field study. The directory must hold kernel-metadata.json and one
percent-format .py source next to its generated .ipynb.
"""
import glob, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def kdir():
    d = sys.argv[2] if len(sys.argv) > 2 else "kaggle"
    path = d if os.path.isabs(d) else os.path.join(HERE, d)
    assert os.path.isfile(os.path.join(path, "kernel-metadata.json")), path
    return path


def kernel_id(path):
    with open(os.path.join(path, "kernel-metadata.json")) as f:
        return json.load(f)["id"]


def cmd(args):
    print("+", " ".join(args))
    r = subprocess.run(args, capture_output=True, text=True,
                       env=dict(os.environ, PYTHONUTF8="1"))
    print(r.stdout)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
    return r


def build(path):
    """py -> ipynb via jupytext, then add the kernelspec Kaggle's papermill requires."""
    src = glob.glob(os.path.join(path, "*.py"))
    assert len(src) == 1, src
    nb_path = src[0][:-3] + ".ipynb"
    cmd([sys.executable, "-m", "jupytext", "--to", "ipynb", src[0]])
    with open(nb_path, encoding="utf-8") as f:
        nb = json.load(f)
    nb["metadata"]["kernelspec"] = {"name": "python3", "display_name": "Python 3",
                                    "language": "python"}
    nb["metadata"]["language_info"] = {"name": "python", "version": "3.12"}
    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1)


def push():
    path = kdir()
    build(path)
    # T4 required: Kaggle's default P100 (sm_60) is unsupported by current torch builds
    cmd([sys.executable, "-m", "kaggle", "kernels", "push", "-p", path,
         "--accelerator", "NvidiaTeslaT4"])


def status():
    cmd([sys.executable, "-m", "kaggle", "kernels", "status", kernel_id(kdir())])


def pull():
    path = kdir()
    dest = sys.argv[3] if len(sys.argv) > 3 else os.path.join(HERE, "results",
                                                              "latest")
    os.makedirs(dest, exist_ok=True)
    cmd([sys.executable, "-m", "kaggle", "kernels", "output", kernel_id(path),
         "-p", dest])


if __name__ == "__main__":
    {"push": push, "status": status, "pull": pull}[sys.argv[1]]()
