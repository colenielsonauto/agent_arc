# Git Workflow Guide

## 📋 Recommended Strategy: Feature Branch Workflow

### Branch Structure
```
main (production-ready code)
├── develop (integration branch)
├── feature/week1-api-foundation
├── feature/week1-llm-integration
├── feature/week2-email-pipeline
└── hotfix/config-loading-fix
```

### Daily Workflow

#### 1. **Start of Day**
```bash
# Pull latest changes
git checkout develop
git pull origin develop

# Create feature branch for your task
git checkout -b feature/week1-api-foundation
```

#### 2. **During Development** (commit frequently!)
```bash
# After each small completion (30min-1hr of work)
git add .
git commit -m "feat: add health check endpoints

- Basic /health endpoint
- Detailed /health/detailed with component status
- Error handling for missing components"

# Push frequently (at least daily)
git push origin feature/week1-api-foundation
```

#### 3. **End of Task**
```bash
# Create pull request via GitHub
# Merge to develop when ready
# Delete feature branch after merge
```

### Commit Message Format
```
type: brief description

Optional longer description
- Bullet points for details
- What changed
- Why it changed

Fixes #123 (if fixing an issue)
```

**Types**: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`

### When to Push/Commit

| Action | When | Example |
|--------|------|---------|
| **Commit** | Every 30-60min of work | "feat: add LLM config validation" |
| **Push** | At least daily | End of work session |
| **PR/Merge** | When task/feature complete | End of week1 task |
| **Tag** | Major milestones | `v1.0.0-mvp`, `v1.1.0-week2` |

### Weekly Rhythm
- **Monday**: Plan week tasks, create feature branches
- **Daily**: Commit frequently, push daily
- **Friday**: Create PRs, merge completed features
- **Weekend**: Merge develop → main if stable

### Emergency/Hotfixes
```bash
# For urgent fixes
git checkout main
git checkout -b hotfix/critical-config-bug
# ... fix ...
git commit -m "fix: resolve configuration loading error"
# Merge directly to main and develop
```

## 🎯 Task-Driven Development

### Link Git to Tasks
```bash
# Branch naming matches tasks
feature/week1-day1-api-foundation
feature/week1-day3-llm-integration
feature/week2-day1-email-pipeline

# Commit messages reference tasks
git commit -m "feat: implement FastAPI health checks

- Completes tasks/mvp/week1_core_integration.md Day 1-2
- Basic health endpoint working
- Component status validation added"
```

### Track Progress
```bash
# Update task files with commits
git add tasks/mvp/week1_core_integration.md
git commit -m "docs: mark API foundation tasks complete

- [x] Create FastAPI app
- [x] Add health check endpoints
- [x] CORS configuration"
```

## 🚀 Recommended Commands

### Setup (one time)
```bash
# Set up develop branch
git checkout -b develop
git push -u origin develop

# Set up .gitignore properly
echo ".venv/" >> .gitignore
echo ".env" >> .gitignore
echo ".secrets/" >> .gitignore
```

### Daily Routine
```bash
# Morning start
git checkout develop && git pull
git checkout -b feature/todays-task

# Evening end
git add . && git commit -m "progress: describe what you did"
git push origin feature/todays-task
```

### Weekly Review
```bash
# See your progress
git log --oneline --since="1 week ago" --author="your-name"

# Create release when ready
git tag -a v1.0.0-mvp -m "MVP Release - Week 1 Complete"
git push origin v1.0.0-mvp
```

## 📊 Progress Tracking

Use GitHub Issues + Projects:
1. **Issues**: Each task from `tasks/mvp/*.md`
2. **Projects**: Kanban board (Todo → In Progress → Done)
3. **PRs**: Link to issues and tasks
4. **Milestones**: Week 1, Week 2, Week 3

This keeps you organized without overkill! 