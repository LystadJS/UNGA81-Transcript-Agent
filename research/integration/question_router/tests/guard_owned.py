"""Git-metadata guard for coordinator full checkouts. No source content is opened."""
import argparse
import json
import subprocess

BASE = "884097997f89b0040e4418480378f077e3b65434"
PREFIX = "research/integration/question_router/"

def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--head", required=True)
    args = parser.parse_args()
    if git("rev-parse", "HEAD") != args.head:
        raise SystemExit("Wrong checkout head")
    subprocess.run(["git", "merge-base", "--is-ancestor", BASE, "HEAD"], check=True)
    paths = git("diff", "--name-only", BASE, "HEAD").splitlines()
    if not paths or not all(path.startswith(PREFIX) for path in paths):
        raise SystemExit("Out-of-scope paths")
    for line in git("ls-tree", "-r", "HEAD", "--", PREFIX).splitlines():
        if not line.startswith("100644 blob "):
            raise SystemExit("Only ordinary source files are allowed")
    print(json.dumps({"head":args.head,"tree":git("rev-parse","HEAD^{tree}"),"c0":BASE,
                      "changed_files":len(paths),"owned_paths":True,"scope":"git_metadata_only"}))

if __name__ == "__main__":
    main()
