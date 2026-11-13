# Container setup

Run `./setup` on Ubuntu with root or passwordless sudo. Setup installs system
dependencies, bootstraps mise if absent, and applies chezmoi. Mise installs the
pinned development tools. The bootstrap still downloads the upstream mise installer.

DevPod can use this repository with
`devpod up . --recreate --dotfiles https://github.com/OWNER/REPOSITORY`.
Use `--dotfiles-script setup` if automatic script detection is unavailable.
Select the reviewed branch or commit until the cleanup PR is merged.
Do not use DevPod for the outbound-only CI runner: its interactive access and
workspace mounts need a separate security review.

Bash remains the default shell. Start `zsh` for Zsh, Oh My Zsh, completion,
autosuggestions, syntax highlighting, fzf, and the Starship prompt. Setup does not
change the login shell, Docker groups, or services. Before applying, setup backs up
existing shell, mise, Neovim, Oh My Zsh, and Safe Chain integration files under
`~/.local/state/dotfiles/backups/` with owner-only access. It does not set a Git
identity. Neither shell loads host
credentials or legacy language managers.

Both shells include `cat` → `bat` (or Ubuntu’s `batcat`) and `ch` → `chezmoi`,
persistent history, and fzf integration. Bash also loads system completion.
Android SDK paths activate only when an SDK exists; an existing `ANDROID_HOME`
takes priority. This setup does not download the Android SDK.

Safe Chain installs through mise. Chezmoi downloads its matching versioned shell
integration, so no `safe-chain setup` installer needs to modify the shell files.
Interactive package-manager commands use Safe Chain when available. Noninteractive
CI scripts do not automatically load these wrappers. Safe Chain is not a sandbox.

Tools live in mise.
Neovim uses the upstream LazyVim starter. Playwright browser binaries are not
installed automatically; install only the browser needed by a project.

Run an installation test only in a disposable Ubuntu environment, not your home.

## Before making this repository public

The cleanup removes personal configuration from the current tree. It does not
remove file history, commit identities, old PR refs, forks, or other clones.
The local history audit found personal identifiers but no credentials. Automated
scans cannot prove that every secret is absent.

Review all history and refs. If historical identities must remain private, publish
a fresh sanitized repository or explicitly approve a coordinated history rewrite.
Revoke any credential found later before publishing. Do not copy host credentials,
SSH keys, tokens, or personal Git identity into this repository or a container image.
