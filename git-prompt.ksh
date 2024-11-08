function git_prompt_info {
    # Check if we're inside a Git repository
    if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        # Get the branch name
        branch=$(git symbolic-ref --short HEAD 2>/dev/null)
        if [[ -z "$branch" ]]; then
            # Detached HEAD, get short commit hash
            branch=$(git rev-parse --short HEAD 2>/dev/null)
        fi
        # Count the number of unstaged changes
        unstaged=$(git status --porcelain 2>/dev/null | grep -c '^ [^ ]')
        # Return the Git information
        echo "($branch|$unstaged)"
    else
        # Not inside a Git repository
        echo ""
    fi
}

function git_prompt_info2 {
    # Check if we're inside a Git repository
    if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        # Get Git status with branch information in porcelain format
        git_status=$(git status --porcelain=2 --branch 2>/dev/null)
        
        # Extract the branch name
        branch=$(echo "$git_status" | sed -n 's/^# branch.head //p')
        if [[ -z "$branch" || "$branch" == "(detached)" ]]; then
            # If on a detached HEAD, get the short commit hash
            branch=$(git rev-parse --short HEAD 2>/dev/null)
        fi
        
        # Count the number of unstaged changes
        unstaged=$(echo "$git_status" | grep -cE '^[12] [^ ]')
        
        # Return the Git information
        echo "($branch|$unstaged)"
    else
        # Not inside a Git repository
        echo ""
    fi
}
