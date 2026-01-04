# 修改commit message作者

### 💻 使用命令行修改

你可以根据是否需要修改提交消息，选择不同的命令：

| 需求场景 | 命令示例 | 说明 |
| :--- | :--- | :--- |
| **修改作者且编辑提交信息** | `git commit --amend --author="新姓名 <新邮箱>"` | 会进入编辑器，可修改提交说明。 |
| **修改作者但不修改提交信息** | `git commit --amend --author="新姓名 <新邮箱>" --no-edit` | 直接更改作者，保留原提交信息。 |
| **使用当前配置的用户信息** | 1. `git config user.name "新姓名"` <br> 2. `git config user.email "新邮箱"` <br> 3. `git commit --amend --reset-author` | `--reset-author` 选项会自动将作者更新为当前配置的用户信息。 |

### ⚠️ 重要注意事项

修改commit信息，尤其是已经推送到远程仓库的commit，需要特别注意：

- **强制推送（Force Push）**：如果你的commit已经推送到了远程仓库（如GitHub、GitLab），在本地修改后，你需要使用强制推送来更新远程记录：`git push --force-with-lease origin <分支名>`。`--force-with-lease` 比 `--force` 更安全，它在覆盖前会检查是否有其他人的新提交，避免意外覆盖同事的工作。

- **协作影响**：**强制推送会重写历史**。如果其他协作者已经基于你旧的commit进行了工作，这可能会给他们的操作带来麻烦。因此，**强烈建议只对尚未推送到远程的commit进行修改**。如果必须修改已推送的commit，请确保通知所有协作者。

### 🔍 检查修改结果
完成修改后，你可以使用 `git log --oneline -1` 命令来查看最新的提交记录，确认作者信息是否已按预期更新
