#!/bin/bash

# Generate the Skills section of README.md from SKILL.md frontmatter.
# Descriptions use YAML multiline `>` syntax — we grab only the first
# indented line after "description:" to keep the table concise.

temp_skills=$(mktemp)

cat >> "$temp_skills" << 'EOF'
| Skill | Description |
|-------|-------------|
EOF

for dir in */; do
  skill_file="${dir}SKILL.md"
  [ -f "$skill_file" ] || continue

  name=$(awk '/^---$/{n++; next} n==1 && /^name:/{print $2; exit}' "$skill_file")

  # Handle both inline (`description: "text"`) and folded block (`description: >`)
  # Folded blocks are joined into a single line.
  desc=$(awk '
    /^---$/ { n++; next }
    n >= 2  { exit }
    n == 1 && /^description:/ {
      sub(/^description: *>? */, "")
      gsub(/"/, "")
      if (length($0) > 0 && $0 != ">") { printf "%s", $0; getline }
      else { getline }
      # Read continuation lines (indented)
      while (/^  +/) {
        sub(/^ +/, "")
        printf " %s", $0
        if (!getline) break
      }
      print ""
      exit
    }
  ' "$skill_file")

  [ -z "$name" ] && continue

  echo "| [${name}](${dir}) | ${desc} |" >> "$temp_skills"
done

echo "" >> "$temp_skills"

# Replace content between markers in README
awk '
  /<!-- SKILLS_START -->/ { print; system("cat '"$temp_skills"'"); skip=1; next }
  /<!-- SKILLS_END -->/ { skip=0 }
  !skip
' README.md > README.md.tmp && mv README.md.tmp README.md

rm "$temp_skills"
