import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parents[1]


class SetupTest(unittest.TestCase):
    def test_install_paths(self):
        for tool in ("chezmoi", "mise", "local-mise", "download"):
            with self.subTest(tool=tool), tempfile.TemporaryDirectory() as directory:
                self.check_install(Path(directory), tool)

    def check_install(self, root, tool):
        source = root / "source with spaces"
        source.mkdir()
        shutil.copy2(SOURCE / "setup", source / "setup")
        self.make_script(source / "manual_deps", 'touch "$HOME/deps-ran"')
        bin_dir = root / "bin"
        bin_dir.mkdir()
        for name in ("dirname", "sh", "touch"):
            (bin_dir / name).symlink_to(shutil.which(name))
        record = 'printf "%s\\n" "$@" > "$HOME/arguments"'
        if tool in ("chezmoi", "mise"):
            self.make_script(bin_dir / tool, record)
        elif tool == "local-mise":
            self.make_script(root / ".local/bin/mise", record)
        self.make_script(
            bin_dir / "curl",
            'if [[ "$*" == *get.chezmoi.io* ]]; then\n'
            f"  printf '%s\\n' '{record}'\n"
            "fi",
        )
        result = subprocess.run(
            ["/bin/bash", str(source / "setup")],
            cwd=root,
            env={**os.environ, "HOME": str(root), "PATH": str(bin_dir)},
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((root / "deps-ran").exists())
        arguments = (root / "arguments").read_text().splitlines()
        expected = ["init", "--apply", "--source", str(source)]
        if tool in ("mise", "local-mise"):
            expected = ["exec", "chezmoi", "--", "chezmoi", *expected]
        self.assertEqual(arguments, expected)

    def test_shell_without_optional_tools(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [shutil.which("zsh"), "-f", "-c", 'source "$1"', "zsh", str(SOURCE / "dot_zshrc")],
                env={**os.environ, "HOME": directory, "PATH": directory},
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, "")

    @staticmethod
    def make_script(path, body):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"#!/bin/bash\nset -eu\n{body}\n")
        path.chmod(0o755)


if __name__ == "__main__":
    unittest.main()
