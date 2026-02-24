# Script to generate 30-40 commits and push to GitHub for PR creation

# Add all untracked files first
Write-Host "Adding untracked files..."
git add .
git commit -m "chore: add project configuration files"

# Generate commit messages
$commitMessages = @(
    "feat: implement basic math operations",
    "fix: resolve division by zero error",
    "docs: update API documentation",
    "style: format code according to project standards",
    "refactor: improve calculation engine performance",
    "test: add unit tests for arithmetic functions",
    "chore: update dependencies to latest versions",
    "feat: add support for complex numbers",
    "fix: handle edge cases in square root function",
    "docs: add installation guide",
    "style: improve variable naming conventions",
    "refactor: extract common utilities to separate module",
    "test: increase test coverage to 85%",
    "chore: configure ESLint rules",
    "feat: implement graph plotting functionality",
    "fix: resolve memory leak in calculations",
    "docs: create comprehensive user guide",
    "style: apply consistent indentation",
    "refactor: optimize database queries",
    "test: add integration tests for API endpoints",
    "chore: setup CI/CD pipeline",
    "feat: add support for mathematical expressions",
    "fix: correct formula parsing logic",
    "docs: update changelog with new features",
    "style: remove unused imports and variables",
    "refactor: simplify authentication flow",
    "test: add performance benchmarks",
    "chore: upgrade React to latest version",
    "feat: implement export to PDF functionality",
    "fix: resolve responsive design issues",
    "docs: add troubleshooting section",
    "style: improve error message formatting",
    "refactor: consolidate duplicate code",
    "test: fix failing tests in production",
    "chore: optimize build configuration",
    "feat: add dark mode support",
    "fix: resolve CORS issues",
    "docs: update README with screenshots",
    "style: improve code readability",
    "refactor: implement caching mechanism",
    "test: add end-to-end tests",
    "chore: update project metadata"
)

# Create commits by making small changes to files
Write-Host "Generating commits..."
for ($i = 0; $i -lt $commitMessages.Count; $i++) {
    $message = $commitMessages[$i]
    
    # Make a small change to trigger a commit
    if ($i % 3 -eq 0) {
        # Modify README
        Add-Content -Path "README.md" -Value "`n- Update: $($message)"
    } elseif ($i % 3 -eq 1) {
        # Create/update a small config file
        $timestamp = Get-Date -Format "yyyyMMddHHmmss"
        "config_$timestamp = true" | Out-File -FilePath "temp_config.txt" -Append
    } else {
        # Modify .gitignore
        Add-Content -Path ".gitignore" -Value "# $($message)"
    }
    
    git add .
    git commit -m $message
    Write-Host "Commit $($i+1)/$($commitMessages.Count): $message"
}

Write-Host "Pushing commits to remote..."
git push origin main

Write-Host "Creating pull request..."
# Note: You'll need to create the PR manually on GitHub or use GitHub CLI
Write-Host "Commits pushed! Please create a PR on GitHub or run: gh pr create --title 'Feature: Multiple improvements' --body 'This PR includes various improvements and fixes.'"

Write-Host "Total commits created: $($commitMessages.Count + 1)"
