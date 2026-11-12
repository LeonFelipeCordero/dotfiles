import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parents[1]


class SetupTest(unittest.TestCase):
    def test_install_paths(self):
        for tool in ("mise", "local-mise", "download"):
            with self.subTest(tool=tool), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source, bin_dir = self.setup_fixture(root)
                record = 'printf "%s\\n" "$@" > "$HOME/arguments"'
                if tool == "mise":
                    self.make_script(bin_dir / "mise", record)
                elif tool == "local-mise":
                    self.make_script(root / ".local/bin/mise", record)
                else:
                    self.make_script(
                        bin_dir / "curl",
                        'while [[ "$1" != --output ]]; do shift; done\n'
                        'printf \'#!/bin/bash\\nmkdir -p "$HOME/.local/bin"\\n'
                        'cp "$HOME/mise-template" "$HOME/.local/bin/mise"\\n\' > "$2"',
                    )
                    self.make_script(root / "mise-template", record)
                result = self.run_setup(source, root, bin_dir)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue((root / "deps-ran").exists())
                self.assertEqual(
                    (root / "arguments").read_text().splitlines(),
                    ["exec", "chezmoi@2.74.1", "--", "chezmoi", "init", "--apply", "--source", str(source)],
                )
                self.assertEqual(list(root.glob("tmp.*")), [])

    def test_failures_stop_setup(self):
        for failure in ("dependencies", "download", "installer", "mise"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source, bin_dir = self.setup_fixture(root)
                if failure == "dependencies":
                    self.make_script(source / "manual_deps", "exit 9")
                elif failure == "download":
                    self.make_script(bin_dir / "curl", "exit 9")
                elif failure == "installer":
                    self.make_script(
                        bin_dir / "curl",
                        'while [[ "$1" != --output ]]; do shift; done\nprintf "exit 9\\n" > "$2"',
                    )
                else:
                    self.make_script(bin_dir / "mise", "exit 9")
                result = self.run_setup(source, root, bin_dir)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((root / "arguments").exists())
                self.assertEqual(list(root.glob("tmp.*")), [])

    def test_existing_configuration_is_backed_up(self):
        with tempfile.TemporaryDirectory(prefix="dotfiles home ") as directory:
            root = Path(directory)
            source, bin_dir = self.setup_fixture(root)
            self.make_script(bin_dir / "mise", ":")
            (root / "personal-nvim").mkdir()
            (root / ".config").mkdir()
            (root / ".config/nvim").symlink_to(root / "personal-nvim", target_is_directory=True)
            paths = (".bashrc", ".config/nvim/lua/config/options.lua", ".oh-my-zsh/custom/plugin.zsh")
            for path in paths:
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("existing configuration")
                target.chmod(0o600)
            result = self.run_setup(source, root, bin_dir)
            self.assertEqual(result.returncode, 0, result.stderr)
            backups = list((root / ".local/state/dotfiles/backups").iterdir())
            self.assertEqual(len(backups), 1)
            for path in paths:
                self.assertEqual((backups[0] / path).read_text(), "existing configuration")
                self.assertEqual((backups[0] / path).stat().st_mode & 0o777, 0o600)
            self.assertFalse((backups[0] / ".config/nvim").is_symlink())
            self.assertEqual(backups[0].stat().st_mode & 0o777, 0o700)

    @unittest.skipUnless(shutil.which("chezmoi"), "chezmoi is required to render the install hook")
    def test_install_hook_uses_home_and_stops_on_failure(self):
        for failure in ("", "trust", "install", "reshim"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory(prefix="dotfiles home ") as directory:
                root = Path(directory)
                self.make_script(
                    root / ".local/bin/mise",
                    'printf "%s\\n" "$*" >> "$HOME/calls"\n'
                    '[[ "$1" != "$FAIL_COMMAND" ]] || exit 9',
                )
                env = {"HOME": directory, "PATH": "/usr/bin:/bin", "FAIL_COMMAND": failure}
                rendered = subprocess.run(
                    [shutil.which("chezmoi"), "--source", str(SOURCE), "execute-template"],
                    input=(SOURCE / ".chezmoiscripts/run_onchange_after_install_packages.sh.tmpl").read_text(),
                    env=env, capture_output=True, text=True,
                )
                self.assertEqual(rendered.returncode, 0, rendered.stderr)
                result = subprocess.run(
                    ["/bin/bash"], input=rendered.stdout, cwd=SOURCE, env=env,
                    capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 9 if failure else 0, result.stderr)
                calls = (root / "calls").read_text().splitlines()
                expected = [f"trust {root}/.config/mise/mise.toml", f"install --cd {root}", "reshim"]
                commands = ["trust", "install", "reshim"]
                count = commands.index(failure) + 1 if failure else len(commands)
                self.assertEqual(calls, expected[:count])

    def test_shells_without_optional_tools(self):
        for shell in ("bash", "zsh"):
            with self.subTest(shell=shell), tempfile.TemporaryDirectory() as directory:
                result = subprocess.run(
                    [shutil.which(shell), "-f", "-c", 'source "$1"', shell, str(SOURCE / f"dot_{shell}rc")],
                    env={"HOME": directory, "PATH": directory},
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, "")

    def test_interactive_shells_find_mise_shims_on_first_command(self):
        for shell in ("bash", "zsh"):
            with self.subTest(shell=shell), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                shims = root / ".local/share/mise/shims"
                for tool in ("mise", "nvim", "starship", "fzf"):
                    self.make_script(shims / tool, 'printf "%s %s\\n" "${0##*/}" "$*" >> "$HOME/calls"')
                self.make_script(root / ".oh-my-zsh/oh-my-zsh.sh", 'printf "omz\\n" >> "$HOME/calls"')
                flags = ["--noprofile", "--norc", "-ic"] if shell == "bash" else ["-fic"]
                result = subprocess.run(
                    [shutil.which(shell), *flags, 'source "$1"; printf "editor=%s\\n" "$EDITOR"',
                     shell, str(SOURCE / f"dot_{shell}rc")],
                    env={"HOME": directory, "PATH": directory, "TERM": "dumb"},
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("editor=nvim", result.stdout)
                calls = (root / "calls").read_text()
                self.assertIn(f"mise activate {shell}", calls)
                self.assertIn(f"starship init {shell}", calls)
                self.assertIn(f"fzf --{shell}", calls)
                if shell == "zsh":
                    self.assertIn("omz", calls)
                self.assertNotIn("command not found", result.stderr)

    def test_shells_do_not_load_personal_credentials_or_change_shell(self):
        for shell in ("bash", "zsh"):
            content = (SOURCE / f"dot_{shell}rc").read_text()
            for forbidden in (".private", "sdkman", "NVM_DIR", "gvm", "safe-chain", "alias cat="):
                self.assertNotIn(forbidden, content)
        content = (SOURCE / "manual_deps").read_text()
        for forbidden in ("chsh", "usermod", "newgrp", "systemctl", "get.docker.com", "devpod"):
            self.assertNotIn(forbidden, content)

    def setup_fixture(self, root):
        source = root / "source with spaces"
        source.mkdir()
        shutil.copy2(SOURCE / "setup", source / "setup")
        self.make_script(source / "manual_deps", 'touch "$HOME/deps-ran"')
        bin_dir = root / "bin"
        bin_dir.mkdir()
        for name in ("dirname", "sh", "touch", "rm", "mkdir", "cp", "mktemp"):
            (bin_dir / name).symlink_to(shutil.which(name))
        return source, bin_dir

    @staticmethod
    def run_setup(source, root, bin_dir):
        return subprocess.run(
            ["/bin/bash", str(source / "setup")],
            cwd=root,
            env={"HOME": str(root), "PATH": str(bin_dir), "TMPDIR": str(root)},
            capture_output=True,
            text=True,
        )

    @staticmethod
    def make_script(path, body):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"#!/bin/bash\nset -eu\n{body}\n")
        path.chmod(0o755)


if __name__ == "__main__":
    unittest.main()
