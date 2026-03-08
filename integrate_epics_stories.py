#!/usr/bin/env python3
"""
Integrate Epics and Stories from _bmad-output/epics-and-stories.md into Archon.

This script:
1. Parses the epics-and-stories.md file
2. Creates a project in Archon for "Techare AI - Epics & Stories"
3. Creates tasks for each story under the corresponding epic
4. Uses the Archon API directly to manage projects and tasks
"""

import asyncio
import json
import re
from pathlib import Path
import httpx
from typing import Optional

# Configuration
API_URL = "http://localhost:8181/api"  # Archon API server
STORIES_FILE = Path("_bmad-output/epics-and-stories.md")


class ArchonIntegration:
    """Handle integration with Archon via HTTP API."""

    def __init__(self, api_url: str):
        self.api_url = api_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def create_project(self, name: str, description: str) -> Optional[str]:
        """Create a project in Archon."""
        print(f"\n📁 Creating project: {name}")
        try:
            response = await self.client.post(
                f"{self.api_url}/projects",
                json={
                    "title": name,  # API expects "title" not "name"
                    "description": description,
                },
            )
            
            if response.status_code == 200:
                result = response.json()
                project_id = result.get("project", {}).get("id")
                print(f"✅ Project created: {project_id}")
                return project_id
            else:
                print(f"❌ Failed to create project (HTTP {response.status_code}): {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error creating project: {e}")
            return None

    async def create_task(
        self,
        project_id: str,
        title: str,
        description: str = "",
        epic: str = "",
        priority: str = "P1",
        estimate: int = 0,
    ) -> Optional[str]:
        """Create a task in Archon."""
        # Build task description with acceptance criteria
        full_description = f"{description}"
        if epic:
            full_description = f"[Epic: {epic}]\n\n{full_description}"

        try:
            response = await self.client.post(
                f"{self.api_url}/tasks",
                json={
                    "project_id": project_id,
                    "title": title,
                    "description": full_description,
                    "assignee": "User",
                    "task_order": self._priority_to_order(priority),
                    "feature": epic,
                },
            )

            if response.status_code == 200:
                result = response.json()
                task_id = result.get("task", {}).get("id")
                print(f"  ✅ Task created: {title} ({task_id})")
                return task_id
            else:
                print(f"  ⚠️  Task creation issue (HTTP {response.status_code}): {response.text}")
                return None
        except Exception as e:
            print(f"  ⚠️  Error creating task: {e}")
            return None

    @staticmethod
    def _priority_to_order(priority: str) -> int:
        """Convert priority string to task order (0-100)."""
        priority_map = {"P1": 90, "P2": 50, "P3": 10}
        return priority_map.get(priority, 50)


class StoriesParser:
    """Parse epics and stories from markdown."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.content = file_path.read_text(encoding="utf-8")

    def extract_epics_and_stories(self) -> dict:
        """Extract epics and their stories from markdown."""
        epics = {}

        # Split content by epic sections
        epic_sections = re.split(r"^## Epic: ", self.content, flags=re.MULTILINE)

        for epic_section in epic_sections[1:]:  # Skip first empty split
            lines = epic_section.split("\n")
            epic_name = lines[0].strip()
            
            # Find goal and scope
            epic_goal = ""
            epic_scope = ""
            goal_match = re.search(r"Goal: (.*?)(?:\n|$)", epic_section)
            if goal_match:
                epic_goal = goal_match.group(1).strip()
            
            scope_match = re.search(r"Scope: (.*?)(?:\n|$)", epic_section)
            if scope_match:
                epic_scope = scope_match.group(1).strip()

            # Find all stories
            stories = {}
            story_pattern = r"^\s*- Story ([A-Z]): (.*?)$"
            
            for story_match in re.finditer(story_pattern, epic_section, re.MULTILINE):
                story_letter = story_match.group(1)
                story_title = story_match.group(2).strip()
                
                # Find acceptance criteria for this story
                start_pos = story_match.end()
                next_story = re.search(r"^\s*- Story [A-Z]:", epic_section[start_pos:], re.MULTILINE)
                end_pos = next_story.start() + start_pos if next_story else len(epic_section)
                
                story_content = epic_section[start_pos:end_pos]
                
                # Extract acceptance criteria
                criteria_match = re.search(r"- Acceptance criteria: (.*?)(?=\n\s*- Tasks:|$)", story_content, re.DOTALL)
                acceptance_criteria = criteria_match.group(1).strip() if criteria_match else ""
                
                # Extract priority and estimate
                priority_match = re.search(r"Priority: (P\d)", story_content)
                priority = priority_match.group(1) if priority_match else "P2"
                
                estimate_match = re.search(r"Estimate: (\d+)\s*pts", story_content)
                estimate = int(estimate_match.group(1)) if estimate_match else 0

                stories[story_letter] = {
                    "title": story_title,
                    "criteria": acceptance_criteria,
                    "priority": priority,
                    "estimate": estimate,
                }

            if stories:
                epics[epic_name] = {
                    "goal": epic_goal,
                    "scope": epic_scope,
                    "stories": stories,
                }

        return epics


async def main():
    """Main integration function."""
    print("🚀 Starting Techare AI Epics & Stories Integration with Archon\n")

    # Initialize integration
    integration = ArchonIntegration(API_URL)

    try:
        # Parse epics and stories
        print("📖 Parsing epics and stories...")
        parser = StoriesParser(STORIES_FILE)
        epics_data = parser.extract_epics_and_stories()

        if not epics_data:
            print("❌ No epics found in the stories file")
            return

        print(f"✅ Found {len(epics_data)} epics\n")

        # Create project
        project_id = await integration.create_project(
            name="Techare AI - Epics & Stories",
            description="Complete breakdown of product epics and user stories for Techare AI Research Project implementation",
        )

        if not project_id:
            print("❌ Failed to create project. Aborting.")
            return

        # Create tasks for each epic and story
        print("\n📝 Creating tasks...\n")
        total_tasks = 0

        for epic_name, epic_data in epics_data.items():
            print(f"\n🎯 Epic: {epic_name}")
            print(f"   Goal: {epic_data['goal']}")

            # Create story tasks
            for story_letter, story_data in epic_data["stories"].items():
                story_id = f"{epic_name.split()[0][0]}-Story-{story_letter}"
                description = f"""**Acceptance Criteria:**
{story_data['criteria']}

**Estimate:** {story_data['estimate']} points
**Priority:** {story_data['priority']}"""

                task_id = await integration.create_task(
                    project_id=project_id,
                    title=f"[Story {story_letter}] {story_data['title']}",
                    description=description,
                    epic=epic_name,
                    priority=story_data["priority"],
                    estimate=story_data["estimate"],
                )
                if task_id:
                    total_tasks += 1

        print(f"\n\n✨ Integration Complete!")
        print(f"📊 Summary:")
        print(f"   - Project ID: {project_id}")
        print(f"   - Total Epics: {len(epics_data)}")
        print(f"   - Total Tasks Created: {total_tasks}")
        print(f"\n🔗 Access Archon at: http://localhost:3737")

    except Exception as e:
        print(f"❌ Integration failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await integration.close()


if __name__ == "__main__":
    asyncio.run(main())
