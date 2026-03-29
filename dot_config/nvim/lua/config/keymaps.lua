-- File: ~/.config/nvim/lua/config/keymaps.lua
local map = vim.keymap.set
local del = vim.keymap.del

-- =============================================================================
-- 1. CLEANUP: Remove conflicting LazyVim defaults
-- =============================================================================
-- Snacks and LazyVim default many of your requested keys to different functions
local keys_to_clear = {
  { "n", "<leader>l" }, -- Default: Lazy UI
  { "n", "<leader>f" }, -- Default: Snacks.find_files
  { "n", "<leader>d" }, -- Default: Debug Menu
  { "n", "<leader>q" }, -- Default: Quit
  { "n", "<leader>e" }, -- Default: Explorer
  { "n", "<leader>E" }, -- Default: Explorer
}

for _, ktc in ipairs(keys_to_clear) do
  pcall(del, ktc[1], ktc[2])
end

-- =============================================================================
-- 2. SETTINGS
-- =============================================================================
vim.opt.visualbell = true
vim.opt.errorbells = false
vim.opt.scrolloff = 5
vim.opt.incsearch = true

-- =============================================================================
-- 3. KEYMAPS (IntelliJ Translation)
-- =============================================================================

-- <leader>q: Close All Editors But Active
map("n", "<leader>q", function()
  Snacks.bufdelete.other()
end, { desc = "Close Other Buffers" })

-- <leader>ha: Hide Active Window
map("n", "<leader>ha", "<cmd>close<cr>", { desc = "Hide Active Window" })

-- <leader>ee: Select in Project View (Reveal current file)
map("n", "<leader>ee", function()
  Snacks.explorer.reveal()
end, { desc = "Reveal in Explorer" })

-- <leader>r: Replace (Current Line)
map("n", "<leader>r", ":s//g<Left><Left>", { desc = "Replace (Line)" })

-- <leader>c: Close Content (Close Buffer)
map("n", "<leader>c", function()
  Snacks.bufdelete()
end, { desc = "Close Buffer" })

-- <leader>a: Show Intention Actions
map("n", "<leader>a", vim.lsp.buf.code_action, { desc = "Code Action" })

-- <leader>i: Goto Implementation
map("n", "<leader>i", vim.lsp.buf.implementation, { desc = "Goto Implementation" })

-- <leader>l: Reformat Code
map("n", "<leader>l", function()
  LazyVim.format({ force = true })
end, { desc = "Reformat Code" })

-- TABS / BUFFERS
map("n", "<S-l>", "<cmd>bnext<cr>", { desc = "Next Buffer" })
map("n", "<S-h>", "<cmd>bprev<cr>", { desc = "Prev Buffer" })

-- NAVIGATION & REFACTORING
map("n", "<S-r>", vim.lsp.buf.rename, { desc = "Rename Element" })
map("n", "<S-p>", function()
  Snacks.picker.grep()
end, { desc = "Find in Path" })
map("n", "<S-f>", function()
  Snacks.picker.files()
end, { desc = "Goto File" })
map("n", "<S-u>", vim.lsp.buf.declaration, { desc = "Goto Declaration" })
