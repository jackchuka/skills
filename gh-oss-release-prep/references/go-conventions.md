# Go Convention Reference

Standard config files for jackchuka's Go repos. Copy from the reference repo listed, then adapt project-specific values (binary name, module path, ldflags).

## Reference repos

- **CLI tools**: `ccli` — has .goreleaser.yaml, .github/workflows (test, license, release), .golangci.yml
- **Libraries**: `go-xcache` — has .github/workflows (test, license only), .golangci.yml, no goreleaser

## .golangci.yml (all Go repos)

```yaml
version: "2"
linters:
  default: standard

formatters:
  enable:
    - goimports
    - gofmt
```

## .gitignore (CLI tools)

```
/<binary-name>
/<binary-name>.exe
dist/
```

## .gitignore (libraries)

```
*.exe
*.exe~
*.dll
*.so
*.dylib
*.test
*.out
.idea/
.vscode/
*.swp
*.swo
.DS_Store
Thumbs.db
```

## .github/dependabot.yml (all Go repos)

```yaml
version: 2
updates:
  - package-ecosystem: "gomod"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
    commit-message:
      prefix: "deps"
      include: "scope"
    reviewers:
      - "jackchuka"
    labels:
      - "dependencies"
      - "go"
    target-branch: "main"
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
    commit-message:
      prefix: "ci"
      include: "scope"
    reviewers:
      - "jackchuka"
    assignees:
      - "jackchuka"
    labels:
      - "dependencies"
      - "github-actions"
    target-branch: "main"
```

## .github/workflows/test.yml (all Go repos)

```yaml
name: Test
on:
  pull_request:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-go@v6
        with:
          go-version-file: "go.mod"
      - run: go mod download
      - uses: golangci/golangci-lint-action@v9
        with:
          version: latest
          args: --timeout=5m
      - run: go test -v ./...
```

## .github/workflows/license.yml (all Go repos)

```yaml
name: Go License Check
on:
  pull_request:
    paths: ["go.mod", "go.sum"]
  push:
    branches: [main]
jobs:
  check-licenses:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-go@v6
        with:
          go-version-file: go.mod
      - run: go install github.com/google/go-licenses@latest
      - run: go-licenses check ./... --include_tests --disallowed_types=permissive,forbidden,restricted
```

## .github/workflows/release.yml (CLI tools only)

```yaml
name: Release
on:
  push:
    tags: ["v*"]
permissions:
  contents: write
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
        with:
          fetch-depth: 0
      - uses: actions/setup-go@v6
        with:
          go-version-file: "go.mod"
      - uses: goreleaser/goreleaser-action@v7
        with:
          args: release --clean
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## .goreleaser.yaml (CLI tools only)

Adapt `binary`, `main`, and `ldflags` per project:

```yaml
version: 2
before:
  hooks:
    - go mod tidy
builds:
  - main: .
    binary: <binary-name>
    env:
      - CGO_ENABLED=0
    goos: [linux, darwin, windows]
    goarch: [amd64, arm64]
    ldflags:
      - -s -w
changelog:
  sort: asc
  filters:
    exclude: ["^docs:", "^test:", "^chore:", "^style:", "^refactor:"]
```

## Common errcheck fixes

When golangci-lint reports errcheck on intentionally-ignored errors:

```go
// Before (fails errcheck):
os.Remove(path)
tmp.Close()

// After:
_ = os.Remove(path)
_ = tmp.Close()
```

Only use `_ =` when the error is genuinely safe to ignore (cleanup, best-effort ops). For errors that matter, handle them properly.
