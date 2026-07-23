---
name: fetch_input
description: Logs in as an admin via the SAOS local API, retrieves all submitted community reports, clears the backend database, and generates a prioritized roadmap for the user to implement.
---

# Fetch Input Skill

When the user requests you to fetch reports or suggests running the "fetch input" skill, you will act as a Product Manager AI. You will hit the `saos-api` backend directly, retrieve all accumulated Bug Reports and Feature Requests, and then wipe them from the server. Finally, you will organize them into a roadmap.

## Workflow Instructions

1. **Write a Retrieval Script**
   - Use your `write_to_file` tool to create a temporary Python script (e.g., `fetch.py` in the root folder).
   - The script should:
     1. Post to `http://192.168.1.45:8003/token` (or the appropriate backend URL if changed) with the payload `username=admin&password=<SAOS_ADMIN_SECRET>` (use the environment variable if present, or ask the user for it if the server is running without it).
     2. With the Bearer token, make a `GET` request to `http://192.168.1.45:8003/admin/reports/fetch_and_clear`.
     3. Print out the JSON array of reports.

2. **Execute and Parse**
   - Run the script using the `run_command` tool.
   - Read the JSON output.

3. **Generate the Roadmap**
   - Categorize the retrieved reports into Critical Bugs and Features.
   - Write out a structured Markdown artifact (e.g., `community_roadmap.md`) that details the step-by-step tasks to implement the feedback.
   - Summarize the roadmap to the user in your message.

4. **Cleanup**
   - Delete the temporary `fetch.py` script.
