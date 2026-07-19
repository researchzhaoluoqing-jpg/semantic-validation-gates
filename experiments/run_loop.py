"""Kaggle experiment loop driver.

Usage (after ~/.kaggle/kaggle.json exists):
    python run_loop.py push      # fill username into kernel-metadata.json, push kernel
    python run_loop.py status    # check run status
    python run_loop.py pull      # download outputs into experiments/results/
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
KDIR = os.path.join(HERE, "kaggle")
META = os.path.join(KDIR, "kernel-metadata.json")
RESULTS = os.path.join(HERE, "results")


def kaggle_username():
    cred = os.path.expanduser("~/.kaggle/kaggle.json")
    with open(cred) as f:
        return json.load(f)["username"]


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


def push():
    user = kaggle_username()
    with open(META) as f:
        meta = json.load(f)
    meta["id"] = f"{user}/semantic-validation-gates-v1"
    with open(META, "w") as f:
        json.dump(meta, f, indent=2)
    cmd([sys.executable, "-m", "kaggle", "kernels", "push", "-p", KDIR])


def status():
    cmd([sys.executable, "-m", "kaggle", "kernels", "status", kernel_id()])


def pull():
    os.makedirs(RESULTS, exist_ok=True)
    cmd([sys.executable, "-m", "kaggle", "kernels", "output", kernel_id(), "-p", RESULTS])


if __name__ == "__main__":
    {"push": push, "status": status, "pull": pull}[sys.argv[1]]()
